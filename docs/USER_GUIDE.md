# User Guide 🧭

Welcome to the Nexus Risk Platform! This guide will help you navigate the dashboard and understand the supply chain risk insights provided by our AI models.

## 1. The Dashboard Interface

The dashboard is your command center for monitoring the Taiwan-US semiconductor supply chain.

### 1.1 Map View 🌍
The central component is the interactive map.
-   **Blue Lines**: Active shipping routes.
-   **Orange/Red Dots**: Ports, colored by congestion level.
-   **Ship Icons**: Real-time position of container vessels.
    -   *Click on a ship* to see details like Speed, Heading, and Destination.

### 1.2 Quick Stats ⚡
Located at the top of the dashboard:
-   **Total Routes**: Number of active monitored lanes.
-   **Avg On-Time %**: Network-wide reliability metric.
-   **High Risk Routes**: Count of routes currently flagged with critical delays.

### 1.3 AI Risk Analyst 🧠
On the right sidebar, you'll find the **AI Summary**.
-   **What it does**: Our XAI (Explainable AI) engine reads raw data (weather, news, satellite) and summarizes it into plain English.
-   **Example**: *"High risk detected due to Typhoon In-Fa approaching Taipei Port. Expect 48h delays."*

---

## 2. Interpreting Risk Scores

Nexus uses a dual-layer risk scoring system. It is important to understand the difference between **Route Risk** and **Network Risk**.

### 2.1 Route Risk (Operational)
*Found in the "Active Routes" table.*

-   **Focus**: A specific ship on a specific path.
-   **Factors**: Current speed, local weather, engine status.
-   **Levels**:
    -   🟢 **Low**: On schedule.
    -   🟡 **Medium**: Minor delays likely (1-2 days).
    -   🔴 **High**: Critical disruption (3+ days delay).

### 2.2 Network Risk (Structural)
*Found in the "Graph Neural Network Analysis" section.*

-   **Focus**: The entire supply chain system.
-   **Factors**: Global port congestion, interconnected dependencies.
-   **Why it matters**: Even if *your* ship is fine, if the destination port (e.g., Los Angeles) is gridlocked, your **Network Risk** will be high (50%+).
-   **Visualization**: The "Network Risk" nodes show which ports are the bottlenecks in the system.

---

## 3. Common Questions (FAQ)

**Q: Why is "Route Risk" Low but "Network Risk" is High?**
A: This is common! Your ship might be sailing perfectly (Low Operational Risk), but heading towards a port that is completely overwhelmed (High Structural Risk). Nexus separates these so you can distinguish between "my ship is broken" vs "the system is broken."

**Q: How often is data updated?**
A:
-   **Vessel Positions**: Every 4 hours.
-   **Weather**: Every 12 hours.
-   **News**: Every 6 hours.

**Q: Can I simulate a disruption?**
A: Yes! Use the "Predict" API endpoint (see technical docs) to ask "What if weather impact increases to 90%?"

---

## 4. Support

For technical support or to report a bug, please open an issue in our [GitHub Repository](https://github.com/veerryait/nexus-risk-platform/issues).
