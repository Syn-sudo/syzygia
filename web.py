
@app.route("/")
def index():
    installed_packages = pkg_manager.list_installed()
    return render_template_string(HTML_TEMPLATE, 
                               installed_packages=installed_packages,
                               search_results=None)

@app.route("/install", methods=["POST"])
def install_package():
    package_name = request.form.get("package_name")
    if package_name:
        pkg_manager.install([package_name])
    return redirect(url_for("index"))

@app.route("/install/<package_name>")
def install_package_get(package_name):
    pkg_manager.install([package_name])
    return redirect(url_for("index"))

@app.route("/remove/<package_name>")
def remove_package(package_name):
    pkg_manager.remove([package_name])
    return redirect(url_for("index"))

@app.route("/upgrade/<package_name>")
def upgrade_package(package_name):
    pkg_manager.upgrade([package_name])
    return redirect(url_for("index"))

@app.route("/search")
def search_packages():
    query = request.args.get("query", "")
    search_results = pkg_manager.search(query) if query else []
    installed_packages = pkg_manager.list_installed()
    return render_template_string(HTML_TEMPLATE,
                               installed_packages=installed_packages,
                               search_results=search_results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

