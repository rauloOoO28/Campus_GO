

## 📖 Description

The **Campus Navigation System** is an application designed to help students, staff, and visitors find routes within a university campus quickly and efficiently.

The system models the campus as a **graph**, where:

- **Nodes** represent buildings or important locations  
- **Edges** represent paths between locations  
- Each connection has a **weight representing distance**

The shortest path is calculated using **Dijkstra's Algorithm**.

The backend is built with **Django**, while the frontend uses **HTML, CSS, and JavaScript** to display the map and routes.

---

## 🎯 Project Goals

- Facilitate navigation within the campus  
- Apply **graph theory concepts**  
- Implement efficient routing algorithms  
- Build a clean architecture between **frontend and backend**  
- Develop a **scalable and well-documented system**

---

## 🧠 Technologies Used

### Backend
- **Python**
- **Django**
- **REST API**
- Implementation of **Dijkstra's Algorithm**

### Frontend
- **HTML**
- **CSS**
- **JavaScript**
- Interactive map visualization

### Version Control
- **Git**
- **GitHub**

---

## 🏗️ Project Architecture

The project is divided into several main modules:

```
campus-navigation-system/
│
├── backend_servidor
├── frontend_interfaz
├── datos_sistema
├── documentacion_proyecto
├── pruebas_sistema
└── scripts_utilidad
```

---

## Backend

Contains:

- API services
- Route calculation logic
- Graph model
- Shortest path algorithm

---

## Frontend

Contains:

- User interface
- Campus map visualization
- Route display between locations

---

## System Data

Contains the campus graph model:

```
datos_sistema/grafo_campus.json
```

This file stores the nodes and connections that represent the campus structure.

---

## 📊 Graph Model

The campus is represented as a **weighted graph**:

- Each **node** represents a building or location.
- Each **edge** represents a path between locations.
- **Weights** represent the distance between nodes.

Example structure:

```
{
  "nodes": ["Library", "Cafeteria", "Building A"],
  "edges": [
    {"from": "Library", "to": "Cafeteria", "distance": 50},
    {"from": "Cafeteria", "to": "Building A", "distance": 30}
  ]
}
```

---

## ⚙️ Installation

Clone the repository:

```
git clone https://github.com/yourusername/campus-navigation-system.git
```

Enter the project directory:

```
cd campus-navigation-system
```

Create a virtual environment:

```
python -m venv venv
```

Activate the virtual environment:

**Windows**

```
venv\Scripts\activate
```

**Linux / Mac**

```
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Run the development server:

```
python manage.py runserver
```

---

## 📡 API Example

Example request to calculate the shortest route:

```
GET /api/route?start=Library&end=BuildingA
```

Example response:

```
{
  "route": ["Library", "Cafeteria", "BuildingA"],
  "total_distance": 80
}
```

---

## 👥 Development Team

This project is developed by a **two-person team**, collaborating on:

- Backend development
- Frontend development
- Graph modeling
- Algorithm implementation

The project uses **Git and GitHub** for version control and collaborative development.

---

## 📌 Features

- Campus graph representation
- Shortest path calculation
- Route visualization on a map
- REST API for route queries
- Modular and scalable architecture

---

## 🚀 Project Status

**Currently under development.**

Future improvements include:

- Interactive campus map
- Mobile-friendly interface
- Real-time navigation
- Multi-building routing


