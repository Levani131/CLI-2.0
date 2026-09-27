import sys
import json

class Task:
    """Blueprint for individual task items."""
    def __init__(self, task_id, title, priority="Medium", is_completed=False):
        self.id = task_id
        self.title = title
        self.priority = priority
        self.is_completed = is_completed  

    def mark_complete(self):
        self.is_completed = True

    def to_dict(self):
        
        return {"id": self.id, "title": self.title,
                "priority": self.priority, "is_completed": self.is_completed}

    @classmethod
    def from_dict(cls, data):
       
        return cls(data["id"], data["title"], data["priority"], data["is_completed"])

    def __str__(self):
        status = "x" if self.is_completed else " "
        return f"[{status}] #{self.id} | {self.title} ({self.priority} Priority)"

    
    def __repr__(self):
        return f"Task({self.id!r}, {self.title!r}, {self.priority!r})"


class UrgentTask(Task):
    """NEW: A Task that is always High priority and prints with a 🔥."""
    def __init__(self, task_id, title, is_completed=False):
        super().__init__(task_id, title, priority="High", is_completed=is_completed)

    def __str__(self):
        return f"🔥 {super().__str__()}"


class TaskManager:
    """Manages a list of Task/UrgentTask instances plus persistence."""
    def __init__(self):
        self.tasks = []
        self._next_id = 1

    def add_task(self, title, priority="Medium", urgent=False):
        
        if urgent:
            new_task = UrgentTask(self._next_id, title)
        else:
            new_task = Task(self._next_id, title, priority)
        self.tasks.append(new_task)
        print(f"✨ Task added: '{title}' with ID #{self._next_id}")
        self._next_id += 1
        
        
        self.save_to_file()

    def list_all_tasks(self):
        if not self.tasks:
            print("📭 No tasks currently registered!")
            return
        print("\n--- CURRENT TASK LIST ---")
        for task in self.tasks:
            print(task)  
        print("-------------------------\n")

    def complete_task(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                task.mark_complete()
                print(f"🎉 Task #{task_id} marked as completed!")
                
             
                self.save_to_file()
                return
        print(f"❌ Error: Task #{task_id} not found.")

    def save_to_file(self, filename="tasks.json"):
        data = [task.to_dict() for task in self.tasks]
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved {len(self.tasks)} tasks to {filename}")

    def load_from_file(self, filename="tasks.json"):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            
            self.tasks = []
            for item in data:
                if item["priority"] == "High":
                    self.tasks.append(UrgentTask(item["id"], item["title"], item["is_completed"]))
                else:
                    self.tasks.append(Task.from_dict(item))
            self._next_id = max((t.id for t in self.tasks), default=0) + 1
            print(f"📂 Loaded {len(self.tasks)} tasks from {filename}")
        except FileNotFoundError:
            print(f"ℹ️ No saved file found at {filename} — starting fresh.")

    def get_stats(self):
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.is_completed)
        print(f"\n📊 STATS: Total: {total} | Completed: {completed} | Pending: {total - completed}\n")


def main():
    manager = TaskManager()
    manager.load_from_file()  

    while True:
        print("=== OOP TASK MANAGER (v2) ===")
        print("1. View All Tasks")
        print("2. Add New Task")
        print("3. Add URGENT Task")  
        print("4. Mark Task Complete")
        print("5. View Summary Stats")
        print("6. Save & Exit")  

        choice = input("\nSelect option (1-6): ").strip()

        if choice == "1":
            manager.list_all_tasks()
        elif choice == "2":
            title = input("Enter task title: ").strip()
            prio = input("Enter priority (Low/Medium/High) [Medium]: ").strip() or "Medium"
            if title:
                manager.add_task(title, prio)
            else:
                print("❌ Title cannot be empty!")
        elif choice == "3":
            title = input("Enter urgent task title: ").strip()
            if title:
                manager.add_task(title, urgent=True)  
            else:
                print("❌ Title cannot be empty!")
        elif choice == "4":
            tid = input("Enter Task ID to complete: ").strip()
            if tid.isdigit():
                manager.complete_task(int(tid))
            else:
                print("❌ Please enter a valid numerical ID.")
        elif choice == "5":
            manager.get_stats()
        elif choice == "6":
            manager.save_to_file()  
            print("👋 Saved! Happy coding.")
            sys.exit(0)
        else:
            print("⚠️ Invalid option. Please enter a number between 1 and 6.")


if __name__ == "__main__":
    main()