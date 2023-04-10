## e-commerce API
A RESTful API for an e-commerce platform that allows customers browse through products, add products to their shopping cart, place orders for those products and purchase them. The API comes with endpoints for managing orders, product reviews, authentication and authorization. It also supports pagination, filtering, etc.


Some features include
1. JWT Authentication and authorization
2. Optimized database queries
2. Interactive Swagger documentation
3. Braintree payment integration
4. Debug toolbar and more...


### Stack
1. Python 3.10
2. Django 4.1.2
3. Django Rest Framework 3.14.0
4. PostgreSQL 12


### Setup
Clone the repository using the git command
```
git clone https://github.com/klvxn/ecommerce-API
```

Navigate into the project's root directory
```
cd ecommerce-API
```

Build the docker images 
```
docker-compose build
```
Run the docker containers
```
docker-compose up
```
<br>

The API will be ready at: `http://localhost:8000/` <br>

Access the documentation at: `http://localhost:8000/swagger/`
<br>
<br>


### API Endpoints Overview
Here are some of the endpoints. <br>
Assuming the local server is running at `http://localhost:8000` 

<br>

#### Authentication
Create a user account
```
POST http://localhost:8000/api/v1/customers/

REQUEST BODY
    {
        "email": "admin@django.com",
        "first_name": "Django",
        "last_name": "Admin",
        "date_of_birth": "2022-10-15",
        "password": "djangorest",
        "password2": "djangorest"
    }
```
<BR> 

Create access token
```
POST http://localhost:8000/auth/token/

REQUEST BODY 
    {
        "email": "admin@django.com",
        "password": "djangorest"
    }
```
<br> 

Logout user
```
POST http://localhost:8000/auth/logout/
```
<br>

Refresh access token
```
POST http://localhost:8000/auth/token/refresh/

REQUEST BODY 

    {"refresh": "your_refresh_token"}
```

<br>


#### Products Endpoints
Retrieve all products or a single product
```
GET http://localhost:8000/api/v1/products/


GET http://localhost:8000/api/v1/products/{id}
```

<br>

Add a product with Id to cart
```
POST http://localhost:8000/api/v1/products/{Id}/add/

REQUEST BODY

    {"quantity": 3}
```

<br>

Remove a product from cart 
```
DELETE http://localhost:8000/api/v1/products/{Id}/delete/
```
<br>


#### Shopping Cart Endpoints
Retrieve items in shopping cart
```
GET http://localhost:8000/api/v1/shopping-cart/
```

<br>

Create an order from user's cart items
```
POST http://localhost:8000/api/v1/shopping-cart/

REQUEST BODY

    {"action": "create_order"}
```
<br>

Update an item in cart
```
PUT http://localhost:8000/api/v1/shopping-cart/

REQUEST BODY 

    {"product_name": 7}
```
<br>

Remove an item from cart <br>
if request body is empty, cart will be cleared.
```
DELETE http://localhost:8000/api/v1/cart/

REQUEST BODY    

    {"product_name": ""}
```
<br>


#### Orders Endpoints
Retrieve all orders or a single order
```
GET http://localhost:8000/api/v1/orders/

GET http://localhost:8000/api/v1/orders/{id}
```
<br>

Update an order with a new address
```
PUT http://localhost:8000/api/v1/orders/{id}/

REQUEST BODY
    {
        "street_address": "Somewhere you live",
        "postal_code": 012345,
        "city": "New Genius",
        "state": "Your state",
        "country": "Your country",
    }
```

<BR>

Delete an order
```
DELETE http://localhost:8000/api/v1/orders/{id}/
```
<BR>



#### Payment Endpoints
Retrieve the template to input payment method details
```
GET http://localhost:8000/api/v1/checkout/order/{id}/
```

Process payment for an order
```
POST http://localhost:8000/api/v1/checkout/order/{id}/make-payment/

REQUEST BODY
    {  
        5555 5555 5555 4444 
        02/24
    }
```
<BR>

Paid orders are exported to a csv file.
If you get an error (e.g. processor declined) while testing payments, check the **[Braintree docs](https://developer.paypal.com/braintree/docs/reference/general/testing/python)**

![(Un)Successful payments in Braintree dashboard](/assets/braintree_dashboard.jpg)


<br>

### Schema 

```
http://localhost:8000/api/v1/openapi/
```

<br>

### Docs 
The documentation for the API and the rest of it's endpoints are available at:

```
http://localhost:8000/swagger/
```
![Swagger Documentation](/assets/swagger_docs.png)

<BR>

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<br>

### Support
If you have any questions or issues with the API, please contact me at [akpulukelvin@gmail.com](mailto:akpulukelvin@gmail.com).