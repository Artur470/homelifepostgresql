from django.db import connections

def test_db_connection():
    # Получение подключения к базе данных
    connection = connections['default']

    # Открытие курсора и выполнение запроса
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        print("Database connection is working. Result:", result)

if __name__ == "__main__":
    test_db_connection()
