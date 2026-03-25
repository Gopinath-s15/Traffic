document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('prediction-form');
    const resultContainer = document.getElementById('result-container');
    const riskBadge = document.getElementById('risk-badge');
    const alertMessage = document.getElementById('alert-message');
    const historyTableBody = document.querySelector('#history-table tbody');

    // Request notification permission on load
    if ("Notification" in window) {
        Notification.requestPermission();
    }

    // Load initial history
    fetchHistory();

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const speed = document.getElementById('speed').value;
        const weather = document.getElementById('weather').value;
        const time = document.getElementById('time').value;

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ speed, weather, time })
            });

            if (!response.ok) {
                throw new Error("Prediction failed");
            }

            const data = await response.json();
            displayResult(data.risk);
            fetchHistory(); // Refresh history

        } catch (error) {
            console.error(error);
            alert("Error predicting risk. Ensure backend is running.");
        }
    });

    function displayResult(riskLevel) {
        resultContainer.classList.remove('hidden');
        riskBadge.textContent = riskLevel;
        
        // Reset classes
        riskBadge.className = 'badge';
        alertMessage.textContent = "";

        if (riskLevel === 'LOW RISK') {
            riskBadge.classList.add('low');
            alertMessage.textContent = "Safe to proceed. Have a good trip!";
        } else if (riskLevel === 'MEDIUM RISK') {
            riskBadge.classList.add('medium');
            alertMessage.textContent = "Take caution. Conditions are slightly risky.";
        } else if (riskLevel === 'HIGH RISK') {
            riskBadge.classList.add('high');
            alertMessage.textContent = "DANGER: High accident risk detected.";
            triggerHighRiskAlerts();
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
                const weatherMap = {0: 'Clear', 1: 'Rainy', 2: 'Foggy/Snow'};
                const timeMap = {0: 'Day', 1: 'Night'};
                
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
