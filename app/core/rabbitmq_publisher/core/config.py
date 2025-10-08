import os
from app.config.settings import settings

rabbitmq_host = settings.rabbitmq_host
rabbitmq_port = settings.rabbitmq_port
rabbitmq_username = settings.rabbitmq_user
rabbitmq_password = settings.rabbitmq_password
rabbitmq_email_sending_quee = settings.rabbitmq_email_sending_queue
rabbitmq_email_sending_exchange = settings.rabbitmq_email_sending_exchange
rabbitmq_email_sending_routing_key = settings.rabbitmq_email_sending_routing_key

