# ---------------------------------------------------------------------------
# Multi-language sample files for onLanguage:* activation events
# ---------------------------------------------------------------------------
# Each language in LANGUAGE_EXTENSIONS should have at least one sample file
# to ensure extensions with onLanguage:* activation events get triggered.
# ---------------------------------------------------------------------------

_LANGUAGE_SAMPLE_FILES: dict[str, str] = {
    # --- TypeScript ---
    "frontend/src/index.ts": """\
import { createApp } from './app';

const API_KEY = process.env.REACT_APP_API_KEY || 'dev-key';

async function main(): Promise<void> {
    const app = createApp({ apiKey: API_KEY });
    await app.start();
    console.log('App started');
}

main().catch(console.error);
""",
    # --- Go ---
    "services/api/main.go": """\
package main

import (
    "fmt"
    "net/http"
    "os"
)

func main() {
    apiKey := os.Getenv("API_KEY")
    if apiKey == "" {
        apiKey = "extrace-default-key"
    }

    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "ok")
    })

    fmt.Println("Starting server on :8080")
    http.ListenAndServe(":8080", nil)
}
""",
    "services/api/go.mod": """\
module github.com/extrace-io/api

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/joho/godotenv v1.5.1
)
""",
    # --- Rust ---
    "services/worker/src/main.rs": """\
use std::env;

fn main() {
    let api_key = env::var("API_KEY").unwrap_or_else(|_| "default".to_string());
    println!("Worker starting with key: {}", &api_key[..8]);

    loop {
        process_job();
        std::thread::sleep(std::time::Duration::from_secs(1));
    }
}

fn process_job() {
    println!("Processing job...");
}
""",
    "services/worker/Cargo.toml": """\
[package]
name = "extrace-worker"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
reqwest = "0.11"
""",
    # --- Java ---
    "services/legacy/src/main/java/io/extrace/App.java": """\
package io.extrace;

public class App {
    private static final String API_KEY = System.getenv("API_KEY");

    public static void main(String[] args) {
        System.out.println("Starting ExTrace Legacy Service");
        if (API_KEY != null && API_KEY.length() >= 8) {
            System.out.println("Key: " + API_KEY.substring(0, 8));
        }
    }
}
""",
    "services/legacy/pom.xml": """\
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>io.extrace</groupId>
    <artifactId>legacy-service</artifactId>
    <version>1.0.0</version>
</project>
""",
    # --- C ---
    "native/parser.c": """\
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    char *api_key = getenv("API_KEY");
    if (api_key == NULL) {
        api_key = "default-key";
    }
    printf("Parser initialized\\n");
    return 0;
}
""",
    # --- C++ ---
    "native/engine.cpp": """\
#include <iostream>
#include <cstdlib>
#include <string>

class Engine {
public:
    void start() {
        const char* key = std::getenv("API_KEY");
        std::cout << "Engine started" << std::endl;
    }
};

int main() {
    Engine engine;
    engine.start();
    return 0;
}
""",
    # --- C# ---
    "services/dotnet/Program.cs": """\
using System;

namespace ExTrace.Service
{
    class Program
    {
        static void Main(string[] args)
        {
            var apiKey = Environment.GetEnvironmentVariable("API_KEY") ?? "default";
            Console.WriteLine("Service starting...");
        }
    }
}
""",
    "services/dotnet/extrace.sln": """\
Microsoft Visual Studio Solution File, Format Version 12.00
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "ExTrace", "ExTrace.csproj", "{12345678-1234-1234-1234-123456789012}"
EndProject
""",
    # --- Ruby ---
    "scripts/migrate.rb": """\
#!/usr/bin/env ruby
require 'pg'

API_KEY = ENV['API_KEY'] || 'default'
puts "Running migrations..."
""",
    "Gemfile": """\
source 'https://rubygems.org'

gem 'pg', '~> 1.5'
gem 'rake', '~> 13.0'
""",
    # --- PHP ---
    "legacy/api.php": """\
<?php
$api_key = getenv('API_KEY') ?: 'default-key';
header('Content-Type: application/json');
echo json_encode(['status' => 'ok']);
""",
    # --- Swift ---
    "mobile/ios/ExTrace/App.swift": """\
import Foundation

struct Config {
    static let apiKey = ProcessInfo.processInfo.environment["API_KEY"] ?? "default"
}

@main
struct ExTraceApp {
    static func main() {
        print("ExTrace iOS starting...")
    }
}
""",
    # --- Kotlin ---
    "mobile/android/app/src/main/kotlin/io/extrace/MainActivity.kt": """\
package io.extrace

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        println("ExTrace Android starting...")
    }
}
""",
    "mobile/android/build.gradle.kts": """\
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "io.extrace"
    compileSdk = 34
}
""",
    # --- HTML ---
    "frontend/public/index.html": """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ExTrace Dashboard</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div id="app"><h1>ExTrace</h1></div>
</body>
</html>
""",
    # --- CSS ---
    "frontend/public/styles.css": """\
:root {
    --primary-color: #2563eb;
    --bg-color: #0f172a;
}

body {
    font-family: 'Inter', sans-serif;
    background: var(--bg-color);
    color: #f8fafc;
}
""",
    # --- XML ---
    "config/settings.xml": """\
<?xml version="1.0" encoding="UTF-8"?>
<settings>
    <database>
        <host>db.extrace.io</host>
        <password>Xk9$mP2vL7nQ</password>
    </database>
</settings>
""",
    # --- Jupyter Notebook (nbformat 4) ---
    "notebooks/analysis.ipynb": """\
{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\\n",
    "\\n",
    "data = list(range(100))\\n",
    "total = sum(data)\\n",
    "print(f\\"Total: {total}\\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Analysis Notebook\\n",
    "Sample notebook for extension activation testing."
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.11.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
""",
}

# ---------------------------------------------------------------------------
# Workspace pattern files for workspaceContains:* activation events
# ---------------------------------------------------------------------------

_WORKSPACE_PATTERN_FILES: dict[str, str] = {
    ".gitignore": """\
node_modules/
vendor/
.venv/
dist/
.env
.env.local
credentials/
*.pem
*.key
""",
    "Makefile": """\
.PHONY: all build test deploy

all: build

build:
\tdocker-compose build

test:
\tpytest tests/

deploy:
\t./scripts/deploy.sh
""",
    "pnpm-workspace.yaml": """\
packages:
  - 'frontend/*'
  - 'services/*'
""",
    "turbo.json": """\
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": { "dependsOn": ["^build"] },
    "test": { "dependsOn": ["build"] }
  }
}
""",
}
