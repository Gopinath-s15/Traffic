document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('prediction-form');
    const resultContainer = document.getElementById('result-container');
    const riskBadge = document.getElementById('risk-badge');
    const alertMessage = document.getElementById('alert-message');
    const historyTableBody = document.querySelector('#history-table tbody');

    let riskMap = null;
    let currentLat = null;
    let currentLon = null;
    let riskCircle = null;

    // Request notification permission on load
    if ("Notification" in window) {
        Notification.requestPermission();
    }

    // Load initial history
    if (historyTableBody) {
        fetchHistory();
    }

    let weatherValue = 0;

    if (form) {
        const locText = document.getElementById('loc-text');
        const weatherText = document.getElementById('weatherText');
        const timeText = document.getElementById('time-text');
        const weatherInput = document.getElementById('weather');
        const timeInput = document.getElementById('time');

        // 1. Time of Day Detection
        const currentHour = new Date().getHours();
        if (currentHour >= 6 && currentHour < 18) {
            timeInput.value = "0";
            if(timeText) timeText.textContent = "Day";
        } else {
            timeInput.value = "1";
            if(timeText) timeText.textContent = "Night";
        }

        // 2. Geolocation with Fast Timeout Configuration
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(position => {
                currentLat = position.coords.latitude;
                currentLon = position.coords.longitude;
                if(locText) locText.textContent = `${currentLat.toFixed(4)}, ${currentLon.toFixed(4)}`;

                fetch(`https://api.openweathermap.org/data/2.5/weather?lat=${currentLat}&lon=${currentLon}&appid=da20b70b86564dea7f48b399c78f8875`)
                .then(res => res.json())
                .then(data => {
                    let weatherStr = data.weather[0].main;
                    console.log("Weather resolved:", weatherStr);
                    
                    let modelWeather = 0;
                    if(weatherStr === "Rain") {
                        weatherValue = 1;
                        modelWeather = 1;
                    } else if (["Snow", "Fog", "Thunderstorm", "Mist"].includes(weatherStr)) {
                        weatherValue = 2;
                        modelWeather = 2;
                    } else {
                        weatherValue = 0;
                        modelWeather = 0;
                    }

                    if (weatherText) weatherText.innerText = weatherStr;
                    if (weatherInput) weatherInput.value = modelWeather.toString();
                }).catch(err => {
                    console.error("OpenWeather API error", err);
                    if (weatherText) weatherText.innerText = "Error Fetching";
                });
            }, (error) => {
                console.warn("Geolocation warning:", error.message);
                if(locText) locText.textContent = "Unavailable / Blocked";
                if(weatherText) weatherText.innerText = "Needs Location Permission";
            }, { enableHighAccuracy: false, timeout: 5000, maximumAge: 300000 });
        } else {
            if(locText) locText.textContent = "Not Supported";
            if(weatherText) weatherText.innerText = "-";
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const speed = document.getElementById('speed').value;
            let weather = weatherValue;
            const time = document.getElementById('time').value;

            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ speed, weather, time })
                });

                if (!response.ok) throw new Error("Prediction failed");

                const data = await response.json();
                displayResult(data.risk);
            } catch (error) {
                console.error(error);
                alert("Error predicting risk.");
            }
        });
    }

    function displayResult(riskLevel) {
        resultContainer.classList.remove('hidden');
        riskBadge.textContent = riskLevel;

        // Reset classes
        riskBadge.className = 'badge';
        alertMessage.textContent = "";

        let mapColor = '#10b981'; // Default Safe Green

        if (riskLevel === 'LOW RISK') {
            riskBadge.classList.add('low');
            alertMessage.textContent = "Safe to proceed. Have a good trip!";
            mapColor = '#10b981';
        } else if (riskLevel === 'MEDIUM RISK') {
            riskBadge.classList.add('medium');
            alertMessage.textContent = "Take caution. Conditions are slightly risky.";
            mapColor = '#f59e0b';
        } else if (riskLevel === 'HIGH RISK') {
            riskBadge.classList.add('high');
            alertMessage.textContent = "DANGER: High accident risk detected.";
            mapColor = '#ef4444';
            triggerHighRiskAlerts();
        }

        // Draw Map Zone
        const mapContainer = document.getElementById('risk-map');
        if (mapContainer && currentLat && currentLon) {
            if (!riskMap) {
                riskMap = L.map('risk-map').setView([currentLat, currentLon], 14);
                L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                    attribution: '&copy; OpenStreetMap & CARTO',
                    subdomains: 'abcd',
                    maxZoom: 20
                }).addTo(riskMap);
            } else {
                riskMap.setView([currentLat, currentLon], 14);
            }

            setTimeout(() => { riskMap.invalidateSize(); }, 300);

            if (riskCircle) riskMap.removeLayer(riskCircle);
            
            riskCircle = L.circle([currentLat, currentLon], {
                color: mapColor,
                fillColor: mapColor,
                fillOpacity: 0.4,
                radius: 400
            }).addTo(riskMap);

            riskCircle.bindPopup(`<b>${riskLevel}</b> Zone`).openPopup();
        }
    }

    function triggerHighRiskAlerts() {
        // 1. Phone Vibration
        if (navigator.vibrate) {
            navigator.vibrate([500, 250, 500, 250, 500]); // Vibrate pattern
        }

        // 2. Voice Alert
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance("Slow down! High accident risk detected.");
            utterance.rate = 1.0;
            utterance.pitch = 1.2;
            utterance.volume = 1;
            window.speechSynthesis.speak(utterance);
        }

        // 3. Mobile / Desktop Notification
        if ("Notification" in window && Notification.permission === "granted") {
            new Notification("HIGH RISK ALERT", {
                body: "Accident risk is high based on current conditions. Please SLOW DOWN.",
                icon: "/static/alert-icon.png" // Placeholder just in case
            });
        }
    }

    async function fetchHistory() {
        try {
            const response = await fetch('/history');
            const data = await response.json();

            historyTableBody.innerHTML = '';

            data.forEach(item => {
                const tr = document.createElement('tr');

                // Formatting weather
                const weatherMap = { 0: 'Clear', 1: 'Rainy', 2: 'Foggy/Snow' };
                const timeMap = { 0: 'Day', 1: 'Night' };

                const wText = weatherMap[item.weather] || 'Unknown';
                const tText = timeMap[item.time] || 'Unknown';

                const timeStr = new Date(item.timestamp).toLocaleString();

                let riskClass = '';
                if (item.risk_level === 'LOW RISK') riskClass = 'status-low';
                else if (item.risk_level === 'MEDIUM RISK') riskClass = 'status-medium';
                else if (item.risk_level === 'HIGH RISK') riskClass = 'status-high';

                tr.innerHTML = `
                    <td>${timeStr}</td>
                    <td>${item.speed}</td>
                    <td>${wText}</td>
                    <td>${tText}</td>
                    <td><span class="status-indicator ${riskClass}">${item.risk_level}</span></td>
                `;

                historyTableBody.appendChild(tr);
            });
        } catch (error) {
            console.error("Failed to fetch history:", error);
        }
    }
});
