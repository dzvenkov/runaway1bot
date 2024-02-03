# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:4-python3.11-appservice
FROM mcr.microsoft.com/azure-functions/python:4-python3.11-slim

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY ./Real-ESRGAN/requirements.txt /requirements_realesrgan.txt
RUN pip install -r ./requirements_realesrgan.txt

COPY . /home/site/wwwroot

WORKDIR /home/site/wwwroot/Real-ESRGAN
RUN python ./setup.py install

WORKDIR /home/site/wwwroot
