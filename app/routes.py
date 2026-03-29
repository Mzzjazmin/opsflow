from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models import Task, Issue, User, ActivityLog

main = Blueprint("main", __name__)


def admin_required():
    if current_user.role != "admin":
        abort(403)


def supervisor_required():
    if current_user.role not in ["admin", "supervisor"]:
        abort(403)


def inputter_required():
    if current_user.role not in ["admin", "inputter"]:
        abort(403)


def log_activity(action, entity_type, entity_id):
    log = ActivityLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        performed_by_id=current_user.id
    )
    db.session.add(log)
    db.session.commit()


# ---------------- DASHBOARD ----------------
@main.route("/dashboard")
@login_required
def dashboard():
    total_tasks = Task.query.count()
    my_tasks_count = Task.query.filter_by(assigned_to_id=current_user.id).count()
    completed_tasks = Task.query.filter_by(status="Completed").count()
    pending_approvals = Task.query.filter_by(approval_status="Pending").count()
    open_issues = Issue.query.filter(Issue.status != "Resolved").count()
    total_users = User.query.count()

    return render_template(
        "dashboard.html",
        total_tasks=total_tasks,
        my_tasks_count=my_tasks_count,
        completed_tasks=completed_tasks,
        pending_approvals=pending_approvals,
        open_issues=open_issues,
        total_users=total_users
    )


# ---------------- USER MANAGEMENT ----------------
@main.route("/users")
@login_required
def users():
    admin_required()
    all_users = User.query.order_by(User.full_name.asc()).all()
    return render_template("users.html", users=all_users)


@main.route("/users/new", methods=["GET", "POST"])
@login_required
def new_user():
    admin_required()

    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        role = request.form.get("role")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("A user with that email already exists.", "danger")
            return render_template("user_form.html")

        user = User(
            full_name=full_name,
            email=email,
            role=role,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        flash("User created successfully.", "success")
        return redirect(url_for("main.users"))

    return render_template("user_form.html")


@main.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    admin_required()
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        role = request.form.get("role")
        password = request.form.get("password")

        existing_user = User.query.filter(User.email == email, User.id != user.id).first()
        if existing_user:
            flash("Another user already has that email.", "danger")
            return render_template("user_edit_form.html", user=user)

        user.full_name = full_name
        user.email = email
        user.role = role

        if password:
            user.password = generate_password_hash(password)

        db.session.commit()

        flash("User updated successfully.", "success")
        return redirect(url_for("main.users"))

    return render_template("user_edit_form.html", user=user)


# ---------------- TASKS ----------------
@main.route("/tasks")
@login_required
def tasks():
    search = request.args.get("search", "")
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")
    assigned_to = request.args.get("assigned_to", "")

    query = Task.query

    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_to:
        query = query.filter(Task.assigned_to_id == int(assigned_to))

    tasks = query.all()
    users = User.query.all()

    return render_template(
        "tasks.html",
        tasks=tasks,
        users=users,
        search=search,
        status=status,
        priority=priority,
        assigned_to=assigned_to
    )


@main.route("/tasks/new", methods=["GET", "POST"])
@login_required
def new_task():
    admin_required()
    users = User.query.all()

    if request.method == "POST":
        assigned_to_id = request.form.get("assigned_to_id")

        task = Task(
            title=request.form["title"],
            description=request.form["description"],
            priority=request.form["priority"],
            assigned_to_id=int(assigned_to_id) if assigned_to_id else None
        )
        db.session.add(task)
        db.session.commit()
        log_activity("Created task", "Task", task.id)

        return redirect(url_for("main.tasks"))

    return render_template("task_form.html", users=users)


@main.route("/tasks/<int:task_id>")
@login_required
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template("task_detail.html", task=task)


@main.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    admin_required()
    task = Task.query.get_or_404(task_id)
    users = User.query.all()

    if request.method == "POST":
        assigned_to_id = request.form.get("assigned_to_id")

        task.title = request.form["title"]
        task.description = request.form["description"]
        task.priority = request.form["priority"]
        task.assigned_to_id = int(assigned_to_id) if assigned_to_id else None

        db.session.commit()
        log_activity("Edited task", "Task", task.id)

        return redirect(url_for("main.task_detail", task_id=task.id))

    return render_template("task_edit_form.html", task=task, users=users)


@main.route("/tasks/<int:task_id>/start")
@login_required
def start_task(task_id):
    inputter_required()
    task = Task.query.get_or_404(task_id)

    task.status = "In Progress"
    db.session.commit()
    log_activity("Started task", "Task", task.id)

    return redirect(url_for("main.task_detail", task_id=task.id))


@main.route("/tasks/<int:task_id>/complete")
@login_required
def complete_task(task_id):
    inputter_required()
    task = Task.query.get_or_404(task_id)

    task.status = "Completed"
    db.session.commit()
    log_activity("Completed task", "Task", task.id)

    return redirect(url_for("main.task_detail", task_id=task.id))


@main.route("/tasks/<int:task_id>/submit")
@login_required
def submit_task(task_id):
    inputter_required()
    task = Task.query.get_or_404(task_id)

    task.approval_status = "Pending"
    db.session.commit()
    log_activity("Submitted task for approval", "Task", task.id)

    return redirect(url_for("main.task_detail", task_id=task.id))


# ---------------- MY TASKS ----------------
@main.route("/my-tasks")
@login_required
def my_tasks():
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")

    query = Task.query.filter_by(assigned_to_id=current_user.id)

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)

    tasks = query.all()

    return render_template(
        "my_tasks.html",
        tasks=tasks,
        status=status,
        priority=priority
    )


# ---------------- APPROVALS ----------------
@main.route("/approvals")
@login_required
def approvals():
    supervisor_required()
    tasks = Task.query.filter_by(approval_status="Pending").all()
    return render_template("approvals.html", tasks=tasks)


@main.route("/tasks/<int:task_id>/approve")
@login_required
def approve_task(task_id):
    supervisor_required()
    task = Task.query.get_or_404(task_id)

    task.approval_status = "Approved"
    task.status = "Completed"
    db.session.commit()
    log_activity("Approved task", "Task", task.id)

    return redirect(url_for("main.approvals"))


@main.route("/tasks/<int:task_id>/reject")
@login_required
def reject_task(task_id):
    supervisor_required()
    task = Task.query.get_or_404(task_id)

    task.approval_status = "Rejected"
    task.status = "In Progress"
    db.session.commit()
    log_activity("Rejected task", "Task", task.id)

    return redirect(url_for("main.approvals"))


# ---------------- ISSUES ----------------
@main.route("/issues")
@login_required
def issues():
    search = request.args.get("search", "")
    status = request.args.get("status", "")
    assigned_to = request.args.get("assigned_to", "")

    query = Issue.query

    if search:
        query = query.filter(Issue.title.ilike(f"%{search}%"))
    if status:
        query = query.filter(Issue.status == status)
    if assigned_to:
        query = query.filter(Issue.assigned_to_id == int(assigned_to))

    issues = query.all()
    supervisors = User.query.filter_by(role="supervisor").all()

    return render_template(
        "issues.html",
        issues=issues,
        supervisors=supervisors,
        search=search,
        status=status,
        assigned_to=assigned_to
    )


@main.route("/issues/new", methods=["GET", "POST"])
@login_required
def new_issue():
    admin_required()
    supervisors = User.query.filter_by(role="supervisor").all()

    if request.method == "POST":
        assigned_to_id = request.form.get("assigned_to_id")

        issue = Issue(
            title=request.form["title"],
            description=request.form["description"],
            status="Assigned for Investigation" if assigned_to_id else "Open",
            raised_by_id=current_user.id,
            assigned_to_id=int(assigned_to_id) if assigned_to_id else None
        )
        db.session.add(issue)
        db.session.commit()
        log_activity("Created issue", "Issue", issue.id)

        return redirect(url_for("main.issues"))

    return render_template("issue_form.html", supervisors=supervisors)


@main.route("/issues/<int:issue_id>")
@login_required
def issue_detail(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    return render_template("issue_detail.html", issue=issue)


@main.route("/issues/<int:issue_id>/edit", methods=["GET", "POST"])
@login_required
def edit_issue(issue_id):
    admin_required()
    issue = Issue.query.get_or_404(issue_id)
    supervisors = User.query.filter_by(role="supervisor").all()

    if request.method == "POST":
        assigned_to_id = request.form.get("assigned_to_id")

        issue.title = request.form["title"]
        issue.description = request.form["description"]
        issue.assigned_to_id = int(assigned_to_id) if assigned_to_id else None

        if issue.assigned_to_id and issue.status == "Open":
            issue.status = "Assigned for Investigation"

        db.session.commit()
        log_activity("Edited issue", "Issue", issue.id)

        return redirect(url_for("main.issue_detail", issue_id=issue.id))

    return render_template("issue_edit_form.html", issue=issue, supervisors=supervisors)


@main.route("/my-investigations")
@login_required
def my_investigations():
    supervisor_required()

    search = request.args.get("search", "")
    status = request.args.get("status", "")

    query = Issue.query.filter_by(assigned_to_id=current_user.id)

    if search:
        query = query.filter(Issue.title.ilike(f"%{search}%"))
    if status:
        query = query.filter(Issue.status == status)

    issues = query.all()

    return render_template(
        "my_investigations.html",
        issues=issues,
        search=search,
        status=status
    )


@main.route("/issues/<int:issue_id>/investigate")
@login_required
def investigate_issue(issue_id):
    supervisor_required()
    issue = Issue.query.get_or_404(issue_id)

    issue.status = "Under Investigation"
    db.session.commit()
    log_activity("Started investigation", "Issue", issue.id)

    return redirect(url_for("main.issue_detail", issue_id=issue.id))


@main.route("/issues/<int:issue_id>/resolve", methods=["GET", "POST"])
@login_required
def resolve_issue(issue_id):
    supervisor_required()
    issue = Issue.query.get_or_404(issue_id)

    if request.method == "POST":
        issue.status = "Resolved"
        issue.resolution_note = request.form.get("resolution_note")
        db.session.commit()
        log_activity("Resolved issue", "Issue", issue.id)

        return redirect(url_for("main.issue_detail", issue_id=issue.id))

    return render_template("issue_resolve_form.html", issue=issue)


@main.route("/issues/<int:issue_id>/escalate", methods=["GET", "POST"])
@login_required
def escalate_issue(issue_id):
    supervisor_required()
    issue = Issue.query.get_or_404(issue_id)

    if request.method == "POST":
        admin_user = User.query.filter_by(role="admin").first()

        issue.status = "Escalated"
        issue.investigation_note = request.form.get("investigation_note")

        if admin_user:
            issue.assigned_to_id = admin_user.id

        db.session.commit()
        log_activity("Escalated issue to admin", "Issue", issue.id)

        return redirect(url_for("main.issue_detail", issue_id=issue.id))

    return render_template("issue_escalate_form.html", issue=issue)


# ---------------- ACTIVITY LOG ----------------
@main.route("/activity")
@login_required
def activity():
    supervisor_required()
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    return render_template("activity.html", logs=logs)


@main.route("/tasks/<int:task_id>/activity")
@login_required
def task_activity(task_id):
    task = Task.query.get_or_404(task_id)
    logs = ActivityLog.query.filter_by(
        entity_type="Task",
        entity_id=task.id
    ).order_by(ActivityLog.timestamp.desc()).all()

    return render_template("entity_activity.html", logs=logs, title=f"Task Activity - {task.title}")


@main.route("/issues/<int:issue_id>/activity")
@login_required
def issue_activity(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    logs = ActivityLog.query.filter_by(
        entity_type="Issue",
        entity_id=issue.id
    ).order_by(ActivityLog.timestamp.desc()).all()

    return render_template("entity_activity.html", logs=logs, title=f"Issue Activity - {issue.title}")


# ---------------- ERROR HANDLER ----------------
@main.app_errorhandler(403)
def forbidden(error):
    return render_template("403.html"), 403