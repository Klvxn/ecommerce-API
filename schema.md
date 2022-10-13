openapi: 3.0.2
info:
  title: ''
  version: ''
paths:
  /cart/:
    get:
      operationId: listCarts
      description: ''
      parameters: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: {}
          description: ''
      tags:
      - cart
    post:
      operationId: createCart
      description: ''
      parameters: []
      requestBody:
        content:
          application/json:
            schema: {}
          application/x-www-form-urlencoded:
            schema: {}
          multipart/form-data:
            schema: {}
      responses:
        '201':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - cart
    put:
      operationId: updateCart
      description: ''
      parameters: []
      requestBody:
        content:
          application/json:
            schema: {}
          application/x-www-form-urlencoded:
            schema: {}
          multipart/form-data:
            schema: {}
      responses:
        '200':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - cart
    delete:
      operationId: destroyCart
      description: ''
      parameters: []
      responses:
        '204':
          description: ''
      tags:
      - cart
  /customers/:
    get:
      operationId: listCustomerCreates
      description: ''
      parameters: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: {}
          description: ''
      tags:
      - customers
    post:
      operationId: createCustomer
      description: ''
      parameters: []
      requestBody:
        content:
          application/json:
            schema: {}
          application/x-www-form-urlencoded:
            schema: {}
          multipart/form-data:
            schema: {}
      responses:
        '201':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - customers
  /customers/{id}/:
    get:
      operationId: retrieveCustomerInstance
      description: ''
      parameters:
      - name: id
        in: path
        required: true
        description: ''
        schema:
          type: string
      responses:
        '200':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - customers
    put:
      operationId: updateCustomerInstance
      description: ''
      parameters:
      - name: id
        in: path
        required: true
        description: ''
        schema:
          type: string
      requestBody:
        content:
          application/json:
            schema: {}
          application/x-www-form-urlencoded:
            schema: {}
          multipart/form-data:
            schema: {}
      responses:
        '200':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - customers
    delete:
      operationId: destroyCustomerInstance
      description: ''
      parameters:
      - name: id
        in: path
        required: true
        description: ''
        schema:
          type: string
      responses:
        '204':
          description: ''
      tags:
      - customers
  /orders/:
    get:
      operationId: listOrders
      description: ''
      parameters: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: {}
          description: ''
      tags:
      - orders
    post:
      operationId: createOrdersList
      description: ''
      parameters: []
      requestBody:
        content:
          application/json:
            schema: {}
          application/x-www-form-urlencoded:
            schema: {}
          multipart/form-data:
            schema: {}
      responses:
        '201':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - orders
  /orders/{id}/:
    get:
      operationId: retrieveOrderInstance
      description: ''
      parameters:
      - name: id
        in: path
        required: true
        description: ''
        schema:
          type: string
      responses:
        '200':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - orders
    delete:
      operationId: destroyOrderInstance
      description: ''
      parameters:
      - name: id
        in: path
        required: true
        description: ''
        schema:
          type: string
      responses:
        '204':
          description: ''
      tags:
      - orders
  /payments/order/{id}/make-payment/:
    get:
      operationId: listPayments
      description: ''
      parameters:
      - name: id
        in: path
        required: true
        description: ''
        schema:
          type: string
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: {}
          description: ''
      tags:
      - payments
    post:
      operationId: createPayment
      description: ''
      parameters:
      - name: id
        in: path
        required: true
        description: ''
        schema:
          type: string
      requestBody:
        content:
          application/json:
            schema: {}
          application/x-www-form-urlencoded:
            schema: {}
          multipart/form-data:
            schema: {}
      responses:
        '201':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - payments
  /products/categories/{slug}/:
    get:
      operationId: retrieveProductsList
      description: ''
      parameters:
      - name: slug
        in: path
        required: true
        description: ''
        schema:
          type: string
      responses:
        '200':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - products
    post:
      operationId: createProductsList
      description: ''
      parameters:
      - name: slug
        in: path
        required: true
        description: ''
        schema:
          type: string
      requestBody:
        content:
          application/json:
            schema: {}
          application/x-www-form-urlencoded:
            schema: {}
          multipart/form-data:
            schema: {}
      responses:
        '201':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - products
  /products/:
    get:
      operationId: listProducts
      description: ''
      parameters: []
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: {}
          description: ''
      tags:
      - products
    post:
      operationId: createProductsList
      description: ''
      parameters: []
      requestBody:
        content:
          application/json:
            schema: {}
          application/x-www-form-urlencoded:
            schema: {}
          multipart/form-data:
            schema: {}
      responses:
        '201':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - products
  /products/{id}/:
    get:
      operationId: retrieveProductInstance
      description: ''
      parameters:
      - name: id
        in: path
        required: true
        description: ''
        schema:
          type: string
      responses:
        '200':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - products
    post:
      operationId: createProductInstance
      description: ''
      parameters:
      - name: id
        in: path
        required: true
        description: ''
        schema:
          type: string
      requestBody:
        content:
          application/json:
            schema: {}
          application/x-www-form-urlencoded:
            schema: {}
          multipart/form-data:
            schema: {}
      responses:
        '201':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - products
    put:
      operationId: updateProductInstance
      description: ''
      parameters:
      - name: id
        in: path
        required: true
        description: ''
        schema:
          type: string
      requestBody:
        content:
          application/json:
            schema: {}
          application/x-www-form-urlencoded:
            schema: {}
          multipart/form-data:
            schema: {}
      responses:
        '200':
          content:
            application/json:
              schema: {}
          description: ''
      tags:
      - products
    delete:
      operationId: destroyProductInstance
      description: ''
      parameters:
      - name: id
        in: path
        required: true
        description: ''
        schema:
          type: string
      responses:
        '204':
          description: ''
      tags:
      - products
  /api-auth/token/:
    post:
      operationId: createTokenObtainPair
      description: 'Takes a set of user credentials and returns an access and refresh
        JSON web

        token pair to prove the authentication of those credentials.'
      parameters: []
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TokenObtainPair'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/TokenObtainPair'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/TokenObtainPair'
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenObtainPair'
          description: ''
      tags:
      - api-auth
  /api-auth/token/refresh/:
    post:
      operationId: createTokenRefresh
      description: 'Takes a refresh type JSON web token and returns an access type
        JSON web

        token if the refresh token is valid.'
      parameters: []
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TokenRefresh'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/TokenRefresh'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/TokenRefresh'
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenRefresh'
          description: ''
      tags:
      - api-auth
components:
  schemas:
    TokenObtainPair:
      type: object
      properties:
        email:
          type: string
        password:
          type: string
          writeOnly: true
      required:
      - email
      - password
    TokenRefresh:
      type: object
      properties:
        refresh:
          type: string
        access:
          type: string
          readOnly: true
      required:
      - refresh
