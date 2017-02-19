from flask import render_template, request
from stroll import app
from stroll import utils


@app.route('/about')
def index():
    return render_template("about.html",
                           )


@app.route('/')
def stroll_input():
    return render_template("input.html")


@app.route('/output')
def stroll_output():
    ntime = request.args.get('stroll_time')
    loc = request.args.get('stroll_loc')

    # convert park
    str_out, loc_out, coord_out = utils.make_grid_of_scores(ntime, loc)

    return render_template("output.html", loc_out=loc_out, str_out=str_out, coord_out=coord_out)
