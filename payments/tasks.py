import csv

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string


@shared_task
def write_trxn_to_csv(order, customer, trxn_id):
    """
    Export paid orders to a csv file
    """
    filename = "assets/paid_orders.csv"
    created = order.created.strftime("%Y-%m-%d %H:%M:%S")
    updated = order.updated.strftime("%Y-%m-%d %H:%M:%S")
    header = [
        "Order Id",
        "Date created",
        "Date paid",
        "Customer",
        "Transaction Id",
        "Cost (USD)",
        "Status",
    ]
    with open(filename, "a", newline="") as csvfile:
        orderwriter = csv.writer(csvfile)

        with open(filename, "r") as csvfile:

            if "Order Id" in csvfile.readline():
                pass
            else:
                orderwriter.writerow(header)

        details = [
            order,
            created,
            updated,
            customer,
            trxn_id,
            order.get_total_cost(),
            order.status,
        ]
        orderwriter.writerow(details)


@shared_task
def send_order_confirmation_email(order):
    customer = order.customer
    subject = "Your Order Confirmation"
    message = render_to_string("order_confirmation_email.html", {"order": order})
    send_mail(subject, message, "futureself@service.com", [customer.email])
