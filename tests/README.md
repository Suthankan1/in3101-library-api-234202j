# Live HTTP verification

Start MySQL and the Spring Boot application first. From the project directory:

```sh
python3 tests/verify_api.py
```

The script sends actual HTTP requests to `http://localhost:8080`. It does not mock the server or use an in-memory database. It creates three identified seed books if absent, exercises the required CRUD and validation sequence, verifies additional error cases and OpenAPI metadata, and leaves at least three books including `234202J` in a title. It deletes only the temporary book it created for the CRUD sequence. Run it only against a disposable lab service.

Actual request bodies, response headers, status codes and response bodies are written to `evidence/api-verification.json`, with a readable summary beside it. The script exits unsuccessfully on any failed assertion. A failed connection produces a failure record rather than invented results. These files do not claim to be Postman screenshots.

Import the JSON collection and optional environment from `postman/` into Postman. On an empty database send the two requests in `00 Setup` once, then send and capture S1-S7 in sequence. S1 automatically saves `bookId` for S3-S6. S5 deletes that book, so S6 must use the same saved id. After S6 is captured, the `99 Restore` helper can leave a third book in the database. Do not run setup repeatedly unless additional books are wanted.

For S8, open `http://localhost:8080/swagger-ui.html`, expand `POST /api/books`, and capture the summary and documented 201 and 400 responses. Use Swagger's **Try it out** and **Execute** to perform the Part D checkpoint as well.
