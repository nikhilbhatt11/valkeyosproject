from faker import Faker

fake = Faker()

def generate_fake_tasks(n: int):
    tasks = []
    
    for _ in range(n):
        task = {
            "title": fake.sentence(nb_words=5),
            "description": fake.text(max_nb_chars=50),
            "status": fake.random_element(elements=["pending", "inprogress", "completed"]),
            "deadline": fake.future_date(end_date="+30d").strftime("%Y-%m-%d"),  
        }
        tasks.append(task)
    return tasks
