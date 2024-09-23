from pymysql import *
from enum import Enum
from contextlib import closing
from utils import DbConfig
import pandas as pd
from sqlalchemy import create_engine


class QueryType(Enum):
    NO_SELECT = 1
    SELECT = 2


# 数据库配置
db_config = DbConfig.DatabaseConfig(
    "localhost", 3306, "root", "2931798419q", "db_douban", "utf8"
)


def query(sql, params, query_type=QueryType.SELECT):
    try:
        conn = db_config.get_connection()
        cursor = conn.cursor()
        params = tuple(params)
        cursor.execute(sql, params)

        if query_type != QueryType.NO_SELECT:
            row_list = cursor.fetchall()
            conn.commit()
            return row_list
        else:
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        # 根据实际情况，你可能需要将异常记录到日志或进行其他处理
        print(f"数据库操作异常：{e}")
        # 根据函数的需求，决定是否需要在异常情况下返回特定值或重新抛出异常
        return None
    finally:
        # 确保在函数结束时关闭数据库连接和游标
        cursor.close()
        conn.close()


def fetch_movie_statistics():
    # 获取数据库连接
    engine = create_engine(
        f"mysql+pymysql://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.db}"
    )

    # 使用pandas从数据库加载数据
    df = pd.read_sql_query("SELECT * FROM tb_movie", engine)

    # 处理多值字段，将其拆分为列表
    df["directors"] = df["directors"].str.split(",")
    df["casts"] = df["casts"].str.split(",")
    df["country"] = df["country"].str.split(",")

    # 统计数据
    total_movies = df.shape[0]
    most_common_director = df["directors"].explode().value_counts().idxmax()
    director_count = df["directors"].explode().value_counts().max()
    most_popular_cast = df["casts"].explode().value_counts().idxmax()
    cast_count = df["casts"].explode().value_counts().max()
    highest_rating = df["rating"].max()
    most_common_country = df["country"].explode().value_counts().idxmax()
    country_count = df["country"].explode().value_counts().max()

    # 返回统计结果
    return {
        "total_movies": total_movies,
        "director_count": director_count,
        "most_popular_cast": most_popular_cast,
        "highest_rating": highest_rating,
        "most_common_country": most_common_country,
    }


# 电影分类统计
def fetch_movie_type_distribution():

    # 使用pandas从数据库加载数据
    df = pd.read_sql_query("SELECT * FROM tb_movie", db_config.get_connection())

    # 处理多值字段，将其拆分为列表
    df["types"] = df["types"].str.split(",")

    # 统计电影类型分布
    type_distribution = df["types"].explode().value_counts()

    # 转换为ECharts所需格式：['类型', 数量]
    echarts_data = [
        {"name": label, "value": value} for label, value in type_distribution.items()
    ]

    return echarts_data


# 电影评分统计
def fetch_movie_rating_distribution():
    # 使用pandas从数据库加载数据
    df = pd.read_sql_query("SELECT * FROM tb_movie", db_config.get_connection())
    # 检查评分是否为整数，如果是浮点数，可以四舍五入
    # if df['rating'].dtype == 'float':
    #     df['rating'] = df['rating'].astype(int)

    # 统计每个评分的电影数量
    rating_distribution = df["rating"].value_counts()

    # 按评分升序排序
    sorted_ratings = rating_distribution.sort_index()

    # 转换为ECharts所需格式：[评分, 数量]
    echarts_data = list(sorted_ratings.items())

    return echarts_data


# 获取电影列表
def fetch_movie_list(title=None, directors=None, page_count=1, page_size=10):
    # 创建基本查询
    query = "SELECT * FROM tb_movie WHERE 1=1"
    params = []

    if title:
        query += " AND title LIKE %s"
        params.append(f"%{title}%")
    if directors:
        # 假设 directors 是以逗号分隔的字符串
        director_list = directors.split(',')
        director_conditions = ' OR '.join([f"directors LIKE %s" for _ in director_list])
        query += f" AND ({director_conditions})"
        for director in director_list:
            params.append(f"%{director}%")

    # 计算分页
    offset = (page_count - 1) * page_size
    query += " LIMIT %s OFFSET %s"
    params.extend([page_size, offset])

    # 使用 pandas 从数据库加载数据
    df = pd.read_sql_query(query, db_config.get_connection(), params=params)

    # 获取总数
    count_query = "SELECT COUNT(*) FROM tb_movie WHERE 1=1"
    count_params = []

    if title:
        count_query += " AND title LIKE %s"
        count_params.append(f"%{title}%")
    if directors:
        director_list = directors.split(',')
        director_conditions = ' OR '.join([f"directors LIKE %s" for _ in director_list])
        count_query += f" AND ({director_conditions})"
        count_params.extend([f"%{director}%" for director in director_list])

    total_count = pd.read_sql_query(count_query, db_config.get_connection(), params=count_params).iloc[0, 0]

    # 转换为字典列表
    movie_list = df.to_dict(orient="records")

    return movie_list, total_count