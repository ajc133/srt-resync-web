from flask import Flask, flash, request, redirect, url_for, send_from_directory, abort
from pathlib import Path
from werkzeug.utils import secure_filename

from srt_resync import modify_file, get_modified_filename

UPLOAD_FOLDER = "./uploads"
CONVERTED_FOLDER = "./converted"
ALLOWED_EXTENSIONS = {"srt"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = Path(UPLOAD_FOLDER)
app.config["CONVERTED_FOLDER"] = Path(CONVERTED_FOLDER)


def allowed_file(filename: str):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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
            filename = secure_filename(file.filename)
            file.save(app.config["UPLOAD_FOLDER"] / filename)
            try:
                modify_file(
                    in_dir=app.config["UPLOAD_FOLDER"],
                    infile_name=filename,
                    out_dir=app.config["CONVERTED_FOLDER"],
                    offset=int(request.form["offset"]),
                    overwrite=False,
                )
            except ValueError:
                abort(400)
            return redirect(
                url_for("download_file", name=get_modified_filename(filename))
            )
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


@app.route("/uploads/<name>")
def download_file(name):
    return send_from_directory(app.config["CONVERTED_FOLDER"], name, as_attachment=True)


app.add_url_rule("/uploads/<name>", endpoint="download_file", build_only=True)
