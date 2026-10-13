# Live demo deployment

The project includes `streamlit_app.py`, a browser-based interface that uses the
same `TaskService`, validation rules, and CSV storage as the original CLI.

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy on Render

1. Sign in to [Render](https://render.com/) with GitHub and authorize the
   `uruj04/task-manager-cli` repository.
2. Create a new **Web Service** and select the repository.
3. Choose **Docker** as the runtime and the **Free** compute plan.
4. Create the service. Render will build the included Dockerfile and show a
   public `onrender.com` URL when it is live.

The demo keeps tasks in a temporary per-session CSV file. It is intentionally
not a hosted personal task database, so data disappears after a session ends or
the free service restarts.
