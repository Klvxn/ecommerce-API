import csv


def write_to_csv(order, customer, trxn_id):
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
