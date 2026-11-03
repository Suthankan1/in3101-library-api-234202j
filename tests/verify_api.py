#!/usr/bin/env python3
"""Exercise the running lab API over HTTP and save genuine request/response records.

No mocks or substitute database are used. Start the Spring Boot application with
MySQL first. Only the book created for S1 is deleted; three identified seed books
are left for inspection. Do not point this script at a production service.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--output", type=Path, default=Path("evidence/api-verification.json"))
    parser.add_argument("--allow-remote", action="store_true", help="Explicitly permit mutations of a non-local test service")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        parser.error("base URL must be an absolute HTTP(S) URL")
    if parsed.hostname not in ("localhost", "127.0.0.1", "::1") and not args.allow_remote:
        parser.error("remote mutation requires --allow-remote and a disposable lab service")
    records = []
    checks = []

    def call(label, method, path, expected, payload=None, raw=None):
        body = raw if raw is not None else (json.dumps(payload) if payload is not None else None)
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = Request(base + path, data=body.encode() if body is not None else None, headers=headers, method=method)
        started = datetime.now(timezone.utc).isoformat()
        try:
            response = urlopen(req, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            response_text = response.read().decode("utf-8")
            status = response.code
            reason = response.reason
            response_headers = dict(response.headers.items())
        try:
            decoded = json.loads(response_text) if response_text else None
        except json.JSONDecodeError:
            decoded = response_text
        records.append({"label": label, "timestamp_utc": started, "request": {"method": method, "url": base + path, "headers": headers, "body": body}, "response": {"status": status, "reason": reason, "headers": response_headers, "body": response_text, "json": decoded}, "expected_status": expected, "status_passed": status == expected})
        assert status == expected, f"{label}: expected {expected}, received {status}: {response_text}"
        checks.append(f"{label}: HTTP {status}")
        return decoded, response_text

    def require(condition, message):
        assert condition, message
        checks.append(message)

    failure = None
    try:
        books, _ = call("Setup: inspect existing books", "GET", "/api/books", 200)
        require(isinstance(books, list), "List endpoint returns a JSON array")
        seeds = [
            {"title": "234202J - Clean Code", "author": "Robert C. Martin", "isbn": "LAB02-234202J-SEED-1", "price": 4500.0},
            {"title": "Effective Java", "author": "Joshua Bloch", "isbn": "LAB02-234202J-SEED-2", "price": 5200.0},
            {"title": "Design Patterns", "author": "Erich Gamma et al.", "isbn": "LAB02-234202J-SEED-3", "price": 6100.0},
        ]
        for seed in seeds:
            if not any(book.get("isbn") == seed["isbn"] for book in books):
                created, _ = call("Setup: seed " + seed["title"], "POST", "/api/books", 201, seed)
                books.append(created)
        seed_reference = next(book for book in books if book.get("isbn") == seeds[0]["isbn"])
        original = {"title": "234202J - REST API Verification", "author": "Suthankan Balenthiran", "isbn": "LAB02-234202J-CRUD", "price": 4500.0}
        created, _ = call("S1 Create a book", "POST", "/api/books", 201, {**original, "id": seed_reference["id"]})
        book_id = created.get("id")
        require(isinstance(book_id, int) and book_id > 0, "Created book has a generated positive numeric id")
        require(book_id != seed_reference["id"], "POST ignores a client-supplied existing id and creates a new row")
        seed_after, _ = call("Verify client id did not overwrite seed", "GET", f"/api/books/{seed_reference['id']}", 200)
        require(seed_after == seed_reference, "POST with client id leaves the existing seed book unchanged")
        require(all(created.get(k) == v for k, v in original.items()), "Create response retains every supplied book field")
        books, _ = call("S2 List all books", "GET", "/api/books", 200)
        require(len(books) >= 3, "S2 contains at least three books")
        require(any("234202J" in b.get("title", "") for b in books), "S2 contains an index-number book")
        fetched, _ = call("S3 Get one book", "GET", f"/api/books/{book_id}", 200)
        require(fetched == created, "S3 returns the created book and id")
        changed = {**original, "title": "234202J - REST API Verification (Updated)", "price": 4750.0}
        updated, _ = call("S4 Update a book", "PUT", f"/api/books/{book_id}", 200, changed)
        require(updated.get("id") == book_id and all(updated.get(k) == v for k, v in changed.items()), "S4 retains id and returns all updated values")
        reread, _ = call("Verify update persisted", "GET", f"/api/books/{book_id}", 200)
        require(reread == updated, "Updated values persist on a separate HTTP read")
        _, deleted_text = call("S5 Delete a book", "DELETE", f"/api/books/{book_id}", 204)
        require(deleted_text == "", "S5 204 response body is empty")
        _, missing_text = call("S6 Get deleted book", "GET", f"/api/books/{book_id}", 404)
        require(missing_text == "", "S6 404 response body is empty")
        call("S7 Blank title validation", "POST", "/api/books", 400, {**original, "title": ""})
        call("Extra: blank author validation", "POST", "/api/books", 400, {**original, "author": " "})
        call("Extra: negative price validation", "POST", "/api/books", 400, {**original, "price": -1})
        call("Extra: malformed JSON", "POST", "/api/books", 400, raw='{"title":')
        call("Extra: invalid update validation", "PUT", f"/api/books/{book_id}", 400, {**original, "title": ""})
        call("Extra: update deleted book", "PUT", f"/api/books/{book_id}", 404, changed)
        call("Extra: delete deleted book", "DELETE", f"/api/books/{book_id}", 404)
        spec, _ = call("OpenAPI document", "GET", "/v3/api-docs", 200)
        paths = spec.get("paths", {})
        require(all(method in paths.get(path, {}) for path, method in [("/api/books", "get"), ("/api/books", "post"), ("/api/books/{id}", "get"), ("/api/books/{id}", "put"), ("/api/books/{id}", "delete")]), "OpenAPI exposes all five CRUD endpoints")
        post = paths["/api/books"]["post"]
        require(post.get("summary") == "Create a book" and {"201", "400"}.issubset(post.get("responses", {})), "OpenAPI POST includes summary plus 201 and 400 responses")
        require("Books" in post.get("tags", []), "OpenAPI POST is grouped under Books")
        books, _ = call("Final state: list books", "GET", "/api/books", 200)
        require(len(books) >= 3 and any("234202J" in b.get("title", "") for b in books), "Final database retains at least three books including the index-number book")
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        result = {"student": "Suthankan Balenthiran", "index": "234202J", "completed_at_utc": datetime.now(timezone.utc).isoformat(), "base_url": base, "evidence_type": "Actual HTTP requests to running Spring Boot service; no screenshots or mocked responses", "passed": failure is None, "checks": checks, "failure": failure, "records": records}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        markdown = ["# Live API verification", "", "Suthankan Balenthiran | 234202J", "", "Evidence: actual HTTP requests. These records are not Postman screenshots.", "", f"Base URL: {base}", f"Completed (UTC): {result['completed_at_utc']}", f"Result: {'PASS' if failure is None else 'FAIL'}", "", "| Case | Request | Expected | Actual |", "| --- | --- | --- | --- |"]
        for record in records:
            request, response = record["request"], record["response"]
            markdown.append(f"| {record['label']} | {request['method']} {request['url']} | {record['expected_status']} | {response['status']} {response['reason']} |")
        markdown += ["", "## Assertions", ""] + ["- " + check for check in checks]
        if failure:
            markdown += ["", "Failure: " + failure]
        args.output.with_suffix(".md").write_text("\n".join(markdown) + "\n")
    print(f"{'PASS' if failure is None else 'FAIL'}: {len(records)} HTTP requests; {len(checks)} checks; evidence: {args.output}")
    if failure:
        raise SystemExit(failure)


if __name__ == "__main__":
    main()
