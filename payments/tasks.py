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
        order_writer = csv.writer(csvfile)
        with open(filename, "r") as csvfile:
            if "Order Id" in csvfile.readline():
                pass
            else:
                order_writer.writerow(header)

        details = [
            order,
            created,
            updated,
            customer,
            trxn_id,
            order.total_cost(),
            order.status,
        ]
        order_writer.writerow(details)


@shared_task
def send_order_confirmation_email(order):
    customer = order.customer
    subject = "Your Order Confirmation"
    message = render_to_string("order_confirmation_email.html", {"order": order})
    send_mail(subject, message, "futureself@service.com", [customer.email])


@shared_task
def update_stock(order, customer):
    """
     Update product stock, sales counts, and customer purchase records for a given order.

    Args:
        order (Order): The order containing items that were purchased.
        customer (Customer): The customer who made the purchase.

    Returns:
        None
    """
    for item in order.items.select_related('product'):
        # update remaining products and quantity sold
        item.product.in_stock -= item.quantity
        item.product.quantity_sold += item.quantity
        item.product.save()
        # update products bought by the customer
        customer.products_bought_count += item.quantity
        if item.product not in customer.products_bought.all():
            customer.products_bought.add(item.product)
        customer.save()
        # update the offers claimed by a customer for each item
        if item.offer:
            item.offer.claimed.add(customer)
