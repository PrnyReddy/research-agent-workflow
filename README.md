# Multi-Agent AI Research Platform

## Overview

This project automates market research workflows using a multi-agent system. It retrieves data from various sources, synthesizes insights, and generates structured reports.

---

## Features

- **Frontend:** Built with Next.js and Material UI for task submission and real-time updates.
- **Backend:** FastAPI with AWS Lambda compatibility for scalable execution.
- **Tools:**  
  - Financial data retrieval  
  - News aggregation  
  - Website content scraping  
  - Internal document search  

---

## Development Setup

- Use `docker-compose` to set up Elasticsearch locally for vector database functionality.

---

## How to Run

1. Clone the repository.
2. Set up the environment using `docker-compose`.
3. Start the FastAPI backend and Next.js frontend.
4. Submit research tasks via the frontend.

---

## Technologies Used

- **Frontend:** Next.js, Material UI  
- **Backend:** FastAPI, Elasticsearch  
- **Other Tools:** Beautiful Soup, PyPDF2, Python-docx  

---

## Future Enhancements

- Add support for more data sources.
- Optimize cloud deployment.
