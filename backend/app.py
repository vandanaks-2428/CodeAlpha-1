from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

def create_database():
    connection = sqlite3.connect("database.db")

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_by INTEGER,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'Pending',
        project_id INTEGER,
        assigned_to INTEGER,
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (assigned_to) REFERENCES users(id)
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        user_id INTEGER,
        comment TEXT NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

    connection.commit()
    connection.close()


create_database()


@app.route("/")
def home():
    return "Project Management Tool Backend is Running!"

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"message": "All fields are required"}), 400

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )

        connection.commit()
        connection.close()

        return jsonify({"message": "Registration successful"}), 201

    except sqlite3.IntegrityError as e:
        connection.close()

        print("DATABASE ERROR:", e)

        return jsonify({"message": "Email already registered"}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, username, email FROM users WHERE email = ? AND password = ?",
        (email, password)
    )

    user = cursor.fetchone()

    connection.close()

    if user:
        return jsonify({
            "message": "Login successful",
            "user_id": user[0],
            "username": user[1],
            "email": user[2]
        }), 200

    return jsonify({"message": "Invalid email or password"}), 401

@app.route("/projects", methods=["GET"])
def get_projects():
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("SELECT id, name, description FROM projects")
    projects = cursor.fetchall()

    connection.close()

    project_list = []

    for project in projects:
        project_list.append({
            "id": project[0],
            "name": project[1],
            "description": project[2]
        })

    return jsonify(project_list)

@app.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, name, description FROM projects WHERE id = ?",
        (project_id,)
    )

    project = cursor.fetchone()

    connection.close()

    if project:
        return jsonify({
            "id": project[0],
            "name": project[1],
            "description": project[2]
        })

    return jsonify({"message": "Project not found"}), 404

@app.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json()

    name = data.get("name")
    description = data.get("description")
    created_by = data.get("created_by")

    if not name:
        return jsonify({"message": "Project name is required"}), 400

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO projects (name, description, created_by) VALUES (?, ?, ?)",
        (name, description, created_by)
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Project created successfully"}), 201

@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()

    title = data.get("title")
    description = data.get("description")
    project_id = data.get("project_id")

    if not title or not project_id:
        return jsonify({"message": "Task title and project are required"}), 400

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (title, description, project_id)
        VALUES (?, ?, ?)
        """,
        (title, description, project_id)
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Task created successfully"}), 201

@app.route("/projects/<int:project_id>/tasks", methods=["GET"])
def get_tasks(project_id):
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, title, description, status FROM tasks WHERE project_id = ?",
        (project_id,)
    )

    tasks = cursor.fetchall()

    connection.close()

    task_list = []

    for task in tasks:
        task_list.append({
            "id": task[0],
            "title": task[1],
            "description": task[2],
            "status": task[3]
        })

    return jsonify(task_list)

@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, title, description, status FROM tasks WHERE id = ?",
        (task_id,)
    )

    task = cursor.fetchone()

    connection.close()

    if task:
        return jsonify({
            "id": task[0],
            "title": task[1],
            "description": task[2],
            "status": task[3]
        })

    return jsonify({"message": "Task not found"}), 404

@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task_status(task_id):
    data = request.get_json()

    status = data.get("status")

    if status not in ["Pending", "In Progress", "Completed"]:
        return jsonify({"message": "Invalid status"}), 400

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE tasks SET status = ? WHERE id = ?",
        (status, task_id)
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Task status updated successfully"}), 200

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Task deleted successfully"}), 200

@app.route("/tasks/<int:task_id>/edit", methods=["PUT"])
def edit_task(task_id):
    data = request.get_json()

    title = data.get("title")
    description = data.get("description")

    if not title:
        return jsonify({"message": "Task title is required"}), 400

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE tasks SET title = ?, description = ? WHERE id = ?",
        (title, description, task_id)
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Task updated successfully"}), 200


@app.route("/tasks/<int:task_id>/comments", methods=["POST"])
def add_comment(task_id):
    data = request.get_json()

    user_id = data.get("user_id")
    comment = data.get("comment")

    if not user_id or not comment:
        return jsonify({"message": "User ID and comment are required"}), 400

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO comments (task_id, user_id, comment) VALUES (?, ?, ?)",
        (task_id, user_id, comment)
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Comment added successfully"}), 201

@app.route("/tasks/<int:task_id>/comments", methods=["GET"])
def get_comments(task_id):
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT comments.id, comments.comment, users.username
        FROM comments
        JOIN users ON comments.user_id = users.id
        WHERE comments.task_id = ?
        ORDER BY comments.id DESC
    """, (task_id,))

    comments = cursor.fetchall()

    connection.close()

    comment_list = []

    for comment in comments:
        comment_list.append({
            "id": comment[0],
            "comment": comment[1],
            "username": comment[2]
        })

    return jsonify(comment_list)

@app.route("/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM comments WHERE id = ?",
        (comment_id,)
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Comment deleted successfully"}), 200


if __name__ == "__main__":
    app.run(debug=True)