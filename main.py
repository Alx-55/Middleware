# Middleware - это многофункциональный промежуточный компонент ПО (может использоватся во многих целях) - перехватывает запрсы и/или
# ответы чтобы выполнить какую-либо логику до или после обработки запроса/ответа. В ЭТОМ ПРОЕКТЕ РЕАЛИЗОВАНЫ ДВА ПРИМЕРА ИСПОЛЬЗОВАНИЯ
# MIDDLEWARE: 1) Ограничение количества запросов пользователя в единицу времени (от одного IP) 2) Логирует время выполнения запроса (в терминале).

from fastapi import FastAPI, Request, Response, HTTPException
import uvicorn
from typing import Callable
import time  # добавим секундомер

app = FastAPI()


# Хранилище истории запросов по IP: {ip: [время1, время2, ...]}
REQUEST_HISTORY: dict[str, list[float]] = {}
RATE_LIMIT = 4       # Макс. 4 запроса...
PER_SECONDS = 120     # ...за 120 секунд


@app.middleware("http")  # сделаем ручку для логирования времени выполнения запроса и ограничения количества запросов пользователем
async def log_time_and_limit_requests(request: Request, call_next: Callable):  # call_next - функция, Сallable - вызываемый объект (асинхронный)
    start = time.perf_counter()  # это функция, используется для высокоточного измерения времени (на обработку запроса); start - начало

    client_ip = request.client.host
    now = time.time()

    history = REQUEST_HISTORY.get(client_ip, [])
    # Оставим только те запросы, которые укладываются в интервал
    history = [t for t in history if now - t < PER_SECONDS]

    if len(history) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Слишком много запросов. Подождите немного.")

    # Добавим текущий запрос в историю
    history.append(now)
    REQUEST_HISTORY[client_ip] = history

    response = await call_next(request)
    end = time.perf_counter() - start  # конец (в определении времени на запрос)
    print(f"Время обработки запроса: {end}")
    return response


@app.get('/users', tags=['Пользователи'])  # ручка для получения id-шника и имени пользователя (выбран как-бы самый простой запрос для
                                        # определения времени его исполнения таймером и подсчёта количества "обращений" к нему пользователем).
async def get_users():
    time.sleep(4)  # для улучшения визуализации времени исполнения этой функции сделаем "заметным" (4 сек.) и результат будем видеть в логе в терминале
    return [{'id': 1, 'name': 'Alexandr'}]


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)