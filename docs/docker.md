本项目使用docker compose管理，需求如下
1. 项目增加dockerfile，需要用uv启动python环境，尽量简单，不用其他文件，例如.dockerignore，构建过程尽量简单，复制必要的目录进入镜像即可
2. 在docker compose中打包dockerfile镜像，不需要外部volume
3. 使用alembic管理数据库，项目启动之前，尝试运行"alembic upgrade head"进行数据库schema的更新，不需要其他管理工具