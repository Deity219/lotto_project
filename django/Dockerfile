FROM python:3.11

# WORKDIR
WORKDIR /app

# COPY로 호스트 파일을 이미지로 복사
COPY requirements.txt /app/

# RUN으로 환경 구축
RUN pip install -r requirements.txt

# 소스 코드 복사
COPY . /app/

# EXPOSE로 포트 공개
EXPOSE 8000

# ENTRYPOINT로 컨테이너 시작 시 실행할 명령
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]