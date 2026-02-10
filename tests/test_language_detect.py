"""Tests for language detection."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.language_detect import detect_language


def test_detect_python():
    code = """
def hello_world():
    print("Hello, world!")

if __name__ == "__main__":
    hello_world()
"""
    assert detect_language(code) == "python"


def test_detect_javascript():
    code = """
const express = require('express');
const app = express();

function handleRequest(req, res) {
    console.log("Request received");
    res.send("Hello");
}
"""
    assert detect_language(code) == "javascript"


def test_detect_typescript():
    code = """
interface User {
    name: string;
    age: number;
    isActive: boolean;
}

const getUser = (id: string): User => {
    return { name: "test", age: 25, isActive: true };
}
"""
    assert detect_language(code) == "typescript"


def test_detect_java():
    code = """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
    assert detect_language(code) == "java"


def test_detect_go():
    code = """
package main

import "fmt"

func main() {
    x := 42
    fmt.Println(x)
}
"""
    assert detect_language(code) == "go"


def test_detect_rust():
    code = """
fn main() {
    let mut x = 5;
    println!("The value is: {}", x);
}

pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
"""
    assert detect_language(code) == "rust"


def test_detect_sql():
    code = """
SELECT u.name, u.email
FROM users u
WHERE u.active = 1
ORDER BY u.created_at DESC;
"""
    assert detect_language(code) == "sql"


def test_detect_unknown():
    code = "just some random text with no code patterns"
    assert detect_language(code) == "unknown"


def test_detect_html():
    code = """
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
    <div class="container">Hello</div>
</body>
</html>
"""
    assert detect_language(code) == "html"


def test_detect_bash():
    code = """#!/bin/bash
echo "Hello World"
if [ -f "$FILE" ]; then
    echo "File exists"
fi
"""
    assert detect_language(code) == "bash"
