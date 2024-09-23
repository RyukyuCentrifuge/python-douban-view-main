from flask import Flask, jsonify, request, session
from flask_cors import CORS
from utils import db_query

app = Flask(__name__)
app.secret_key = "mysessionkey"


CORS(app)

@app.before_request
def before_request():
    if (
            request.path.startswith("/static")
            or request.path in ["/api/login", "/api/logout", "/api/register"]
    ):
        return
    print(session.get("login_username"))
    if not session.get("login_username"):
        return jsonify({"error": "未授权"}), 401


@app.route("/api/movie-stats")
def movie_stats():
    # print(db_query.fetch_movie_statistics())
    # print(db_query.fetch_movie_type_distribution())
    # print(db_query.fetch_movie_rating_distribution())
    stats = db_query.fetch_movie_statistics()
    type_distribution = db_query.fetch_movie_type_distribution()
    rating_distribution = db_query.fetch_movie_rating_distribution()

    result = jsonify({
        "code": '200',
        "data": {
            "movieStatistics": {
                "total_movies": int(stats['total_movies']),
                "director_count": int(stats['director_count']),
                "most_popular_cast": stats['most_popular_cast'],
                "highest_rating": stats['highest_rating'],
                "most_common_country": stats['most_common_country']
            },
            "typeDistribution": type_distribution,
            "ratingDistribution": [
                {"rating": str(r[0]), "count": r[1]} for r in rating_distribution
            ]
        }
    })
    return result, 200
    # return jsonify(db_query.fetch_movie_statistics())


@app.route("/api/login", methods=["POST"])
def login():
    req_params = request.json
    sql = "SELECT * FROM `tb_user` WHERE `username` = %s AND `password` = %s"
    params = (req_params["username"], req_params["password"])
    if len(db_query.query(sql, params)) > 0:
        session["login_username"] = req_params["username"]
        return jsonify({"code": "200", "message": "登录成功"})
    return jsonify({"error": "用户名或密码错误"}), 400


@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("login_username", None)
    return jsonify({"message": "已退出登录"})


@app.route("/api/register", methods=["POST"])
def register():
    req_params = request.json
    if req_params["password"] == req_params["password_confirm"]:
        sql = "SELECT * FROM `tb_user` WHERE `username` = %s"
        params = (req_params["username"],)
        if len(db_query.query(sql, params)) > 0:
            return jsonify({"error": "用户名已存在"}), 400
        sql = "INSERT INTO `tb_user` (`username`, `password`) VALUES (%s, %s)"
        db_query.query(sql, (req_params["username"], req_params["password"]), db_query.QueryType.NO_SELECT)
        return jsonify({"message": "注册成功"})
    return jsonify({"error": "两次密码输入不一致"}), 400


@app.route("/api/movies")
def movie_list():
    title = request.args.get('title')
    directors = request.args.get('directors')
    page_count = int(request.args.get('pageCount', 1))
    page_size = int(request.args.get('pageSize', 10))

    if page_count <= 0 or page_size <= 0:
        return jsonify({"error": "pageCount and pageSize must be greater than 0"}), 400

    movies, total_count = db_query.fetch_movie_list(title, directors, page_count, page_size)

    result = jsonify({
        "code": 200,
        "data": {
            "results": movies,
            "totalCount": int(total_count)
        }
    })
    return result, 200
    # movies = db_query.fetch_movie_list()
    # return jsonify(movies)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8003, debug=True)
