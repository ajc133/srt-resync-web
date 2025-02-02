from typing import Any, Generator

from flask import (
    Flask,
    Response,
    flash,
    redirect,
    request,
)

from srt_resync import resync_line

ALLOWED_EXTENSIONS = {"srt"}

app = Flask(__name__)


def allowed_file(filename: str):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def resync_file(lines: list[str], offset: float) -> Generator[str, Any, None]:
    for line in lines:
        decoded = line.decode("utf-8")
        yield resync_line(decoded, offset)


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            try:
                lines = file.stream.readlines()
                offset = float(request.form["offset"])
                return Response(
                    resync_file(lines, offset),
                    mimetype="text/plain",
                    headers={"Content-Disposition": "attachment;filename=resynced.srt"},
                )
            except ValueError:
                return "Invalid offset value", 400
    return """
    <!doctype html>
    <title>Resync SRT File</title>
    <h1>Resync SRT File</h1>
    <style>
    #offset {
      width: 200px;
    }
    </style>
    <form method=post enctype=multipart/form-data>
      <input
        id=offset
        type=number
        name=offset
        max=86400
        min=-86400
        placeholder='Seconds to add or subtract'
        width=100px>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    """
