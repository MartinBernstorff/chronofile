FROM python:3.12
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Run main.py when the container launches
CMD ["python", "src/main.py"]
