## e-commerce API
Using django/django rest framework to design an e-commerce API using Braintree as payment gateaway for credit card purchases.

The API includes 
1. JWT Authentication 
2. Interactive Swagger documentation
3. Braintree payment gateway integration
4. Debug toolbar and more...


### Requirements
1. Python
2. Django
3. Django Rest Framework


### Setup
Clone the repository using the git command
```
git clone https://github.com/klvxn/ecommerce-API
```

Enter into the project's root directory
```
cd ecommerce-API
```

Build the docker images and start the containers
```
docker-compose up
```
The API will be ready at localhost:8000


### API Endpoints 
The various endpoints for the API.
Assuming the local server is running at http://localhost:8000


#### Authentication
Create a user account
```
POST http://localhost:8000/api/v1/customers/

Request body
{
    "email": "admin@django.com",
    "first_name": "Django",
    "last_name": "Admin",
    "date_of_birth": "2022-10-15",
    "password": "djangorest",
    "password2": "djangorest"
}
```

Login into user account
```
POST http://localhost:8000/api/v1/api-auth/login/

Request body 
{
    "email": "admin@django.com",
    "password": "djangorest"
}
```

Logout of user account
```
POST http://localhost:8000/api/v1/api-auth/logout/
```

Retrieve access token for user
```
POST http://localhost:8000/api/v1/api-auth/token/

Request body 
{
    "email": "admin@django.com",
    "password": "djangorest"
}
```

Refresh access token for user
```
POST http://localhost:8000/api/v1/api-auth/token/refresh/
```

#### Products 
Retrieve all products or a single product
```
GET http://localhost:8000/api/v1/products/


GET http://localhost:8000/api/v1/products/{id}
```

Add a product with Id to cart
```
POST http://localhost:8000/api/v1/products/{Id}/

Request body
{
    "quantity": 3
}
```

Remove a product from cart 
```
DELETE http://localhost:8000/api/v1/products/{Id}/
```


#### Cart 
Retrieve cart
```
GET http://localhost:8000/api/v1/cart/
```

Create an order from user's cart if the user wants to save it for later
```
POST http://localhost:8000/api/v1/cart/
```

Update an item in cart
```
PUT http://localhost:8000/api/v1/cart/

Request body 
{
    "product_name": 7 (new quantity)
}
```

Remove an item from cart
```
DELETE http://localhost:8000/api/v1/cart/

Request body 
{
    "product_name": ""
}
if request body is empty, cart will be cleared.
```


#### Orders 
Retrieve all orders or a single order
```
GET http://localhost:8000/api/v1/orders/

GET http://localhost:8000/api/v1/orders/{id}
```

Create an order from user's cart
```
POST http://localhost:8000/api/v1/orders/

Request body
{
    "street_address": "Somewhere you live",
    "postal_code": 012345,
    "city": "New Genius",
    "state": "Your state",
    "country": "Your country",
}
```

Delete an order
```
DELETE http://localhost:8000/api/v1/orders/{id}/
```


#### Payment
Retrieve the template to input payment method details
```
GET http://localhost:8000/api/v1/checkout/order/{id}/make-payment/
```

Process payment for an order
```
POST http://localhost:8000/api/v1/checkout/order/{id}/make-payment/

Request body
{  
    5555 5555 5555 4444 
    02/24
}
```
Paid orders are exported to a csv file.
If you get an error (e.g. processor declined) while testing payments, check the **[Braintree docs](https://developer.paypal.com/braintree/docs/reference/general/testing/python)**

![(Un)Successful payments in Braintree dashboard](/assets/braintree_dashboard.jpg)

### Docs 
The documentation for the API and the rest of it's endpoints are available at:

```
http://localhost:8000/api/v1/swagger/
```
### Schema 

```
http://localhost:8000/api/v1/openapi/
```

![Swagger Documentation](/assets/swagger_docs.png)

