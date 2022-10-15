## e-commerce API
Using django/django rest framework to design an e-commerce API using braintree as payment gateaway for credit card purchases. 

The API includes 
1. Authentication using Json Web Tokens
2. Swagger documentation 
3. Braintree payment gateway integration 


### Requirements
1. Python
2. Django
3. Django Rest Framework

### API Endpoints 
The various endpoints for the API.
Assuming the local server is running on 127.0.0.1:8000


#### Authentication
Create a user account
```
POST http://127.0.0.1:8000/api/v1/customers/
```

Login and logout of user account
```
POST http://127.0.0.1:8000/api/v1/api-auth/login/

POST http://127.0.0.1:8000/api/v1/api-auth/login/
```

Retrieve access token for user
```
POST http://127.0.0.1:8000/api/v1/api-auth/token/
```

Refresh access token for user
```
POST http://127.0.0.1:8000/api/v1/api-auth/token/refresh/
```

#### Products 
View all available products, search for a product or add a particular product to cart.

Retrieve all products or a single product
```
GET http://127.0.0.1:8000/api/v1/products/

GET http://127.0.0.1:8000/api/v1/products/{id}

```

Search for a paticular product
```
GET http://127.0.0.1:8000/api/v1/products/?search=nike

```

Add a product with Id to cart
```
POST http://127.0.0.1:8000/api/v1/products/{Id}/

request body
    {
        "quantity": 3
    }
```

Remove a product from cart 
```
DELETE http://127.0.0.1:8000/api/v1/products/{Id}/

```


#### Cart 
Retrieve a user's cart, update the cart, remove items from the cart and delete the cart

Retrieve cart
```
GET http://127.0.0.1:8000/api/v1/cart/

```

Create an order from user's cart if the user wants to save it for later
```
POST http://127.0.0.1:8000/api/v1/cart/

```

Update an item in cart
```
PUT http://127.0.0.1:8000/api/v1/cart/

request body 
    {
        "product_name": 7 (new quantity)
    }

```

Remove an item from cart
```
DELETE http://127.0.0.1:8000/api/v1/cart/

request body 
    {
        "product_name": " "
    }

    if request body is empty, cart will be deleted.
```


#### Orders 
Retrieve a user's orders, create an order from user'cart

Retrieve all orders or a single order
```
GET http://127.0.0.1:8000/api/v1/orders/

GET http://127.0.0.1:8000/api/v1/orders/{id}

```

Create an order from user's cart
```
POST http://127.0.0.1:8000/api/v1/orders/

request body 
    {
        "street_address": "Somewhere you live",
        "postal_code": 012345,
        "city": "New Genius",
        "state": ,
        "country": ,
    }
```

Filter user's orders based on status (unpaid, paid, delivered)
```
GET http://127.0.0.1:8000/api/v1/orders/?status=paid

```

Delete an order
```
DELETE http://127.0.0.1:8000/api/v1/orders/{id}/

```


#### Payment
Making payment for a particular order using braintree

Retrieve the template to input credit card details
```
GET http://127.0.0.1:8000/api/v1/checkout/orders/{id}/make-payment/

```

Process payment for an order
```
POST http://127.0.0.1:8000/api/v1/checkout/orders/{id}/make-payment/

request body: 
    {  
        card number 
        exp date
    }
```


### Docs 
The documentation for the API and it's the rest of t's endpoints is available at:

```
http://127.0.0.1:8000/api/v1/swagger/

```
### Schema 

```
http://127.0.0.1:8000/api/v1/openapi/

```