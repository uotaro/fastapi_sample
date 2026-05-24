#!/bin/bash
# =============================================================================
# run_fastapi_server.sh
# FastAPI Server の起動・停止・状態確認・ログ表示スクリプト
#
# 使い方:
#   bash run_fastapi_server.sh start    # サーバー起動
#   bash run_fastapi_server.sh stop     # サーバー停止
#   bash run_fastapi_server.sh status   # 稼働状況を表示
#   bash run_fastapi_server.sh log      # 直近のログをリアルタイム表示
# =============================================================================

# ---- 設定変数 ----
# このスクリプトが置かれているディレクトリをプロジェクトルートとする
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"

# ---- .env 読み込み ----
if [[ -f "${PROJECT_ROOT}/.env" ]]; then
  # コメント行・空行を除外して export する
  set -o allexport
  # shellcheck disable=SC1090
  source <(grep -v '^\s*#' "${PROJECT_ROOT}/.env" | grep -v '^\s*$')
  set +o allexport
fi

# アプリケーションの設定（.env の値を優先し、未設定時はデフォルト値を使う）
APP_MODULE="app.main:app"             # uvicorn に渡すモジュール指定
HOST="0.0.0.0"                        # LAN 内の他マシンからもアクセス可能  
PORT="${FASTAPI_SERVER_PORT:-51485}"  # 使用ポート番号

# ログ・PID ファイルのパス
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/${LOG_FILENAME}"
UVICORN_LOG_FILE="${LOG_DIR}/fastapi_uvicorn.log"   # ← uvicornのログは分けよっかな
PID_FILE="${PROJECT_ROOT}/fastapi_server.pid"
LOG_LEVEL="${LOG_LEVEL:-debug}"

# 仮想環境に入るためのコマンド
# ※ sing-ai2_202605 コマンドで仮想環境に入ることが可能
VENV_COMMAND="sing-ai2_202605"

# ---- 色付き出力用エスケープコード ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color（リセット）


# =============================================================================
# ヘルパー関数
# =============================================================================

# ログディレクトリがなければ作成する
ensure_log_dir() {
    mkdir -p "${LOG_DIR}"
    mkdir -p "${LOG_DIR}/old_logs"   # 過去ログ保管フォルダ作成
    logrotate ./logrotate/logrotate.conf -s ./logrotate/logrotate.status
}

# ログローテート
rotate_logs() {
    logrotate "${PROJECT_ROOT}/logrotate/logrotate.conf" \
              -s "${PROJECT_ROOT}/logrotate/logrotate.status"
}

# 仮想環境に入っているかどうかを確認する
# 仮想環境に入っている場合: VIRTUAL_ENV 環境変数が設定されている
# Singularity コンテナ環境の場合: SINGULARITY_CONTAINER が設定されている
is_in_venv() {
    # Singularity コンテナ環境（sing-ai2_202605）の場合
    if [ -n "${SINGULARITY_CONTAINER}" ]; then
        return 0  # 0 = true（シェルスクリプトでは 0 が「成功/真」）
    fi
    # 通常の Python 仮想環境（venv / conda など）の場合
    if [ -n "${VIRTUAL_ENV}" ] || [ -n "${CONDA_DEFAULT_ENV}" ]; then
        return 0
    fi
    return 1  # 1 = false（仮想環境に入っていない）
}

# 現在の PID を取得する（PID ファイルから読み込む）
get_pid() {
    if [ -f "${PID_FILE}" ]; then
        cat "${PID_FILE}"
    else
        echo ""
    fi
}

# プロセスが実行中かどうかを確認する
is_running() {
    local pid
    pid=$(get_pid)
    # ポートが Listen されていれば稼働中
    if lsof -ti tcp:"${PORT}" 2>/dev/null | grep -q .; then
        return 0
    fi
    return 1  # 停止中
}


# =============================================================================
# start: サーバー起動
# =============================================================================
start_server() {
    echo -e "${CYAN}=== FastAPI Server 起動 ===${NC}"

    # すでに起動中かどうかを確認
    if is_running; then
        local pid
        pid=$(get_pid)
        echo -e "${YELLOW}⚠ サーバーはすでに起動中です (PID: ${pid})${NC}"
        echo "  停止するには: bash ${0} stop"
        exit 0
    fi

    # ログディレクトリを準備
    ensure_log_dir

    # ログローテート
    rotate_logs

    # プロジェクトルートに移動（uvicorn がモジュールを正しく見つけられるよう）
    cd "${PROJECT_ROOT}" || {
        echo -e "${RED}❌ プロジェクトルートへの移動に失敗しました: ${PROJECT_ROOT}${NC}"
        exit 1
    }

    # スクリプト自身のパスを確定しておく（ログ表示メッセージ用）
    local SCRIPT_PATH
    SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"

    # 仮想環境の確認
    if is_in_venv; then
        echo -e "${GREEN}✔ 仮想環境（または Singularity コンテナ）を確認しました${NC}"
        # 仮想環境内にいるので uvicorn をそのまま nohup バックグラウンド起動する
        _launch_uvicorn_direct "${SCRIPT_PATH}"
    else
        echo -e "${YELLOW}⚠ 仮想環境に入っていません。${VENV_COMMAND} で仮想環境に入ります...${NC}"
        # -----------------------------------------------------------------
        # 【重要】Singularity コンテナの場合、コンテナ内で nohup & すると
        # コンテナセッション終了後に squashfuse_ll が切断され、
        # torch などのライブラリファイルが読めなくなって起動失敗する。
        #
        # 解決策: コンテナ起動コマンド全体を nohup でバックグラウンド化する。
        # uvicorn はコンテナ内でフォアグラウンド実行し、
        # コンテナプロセスごと nohup で切り離すことでファイルシステムが
        # セッション終了後も維持される。
        # -----------------------------------------------------------------
        echo "  起動コマンド: python -m uvicorn ${APP_MODULE} --host ${HOST} --port ${PORT}"
        echo "  ログ出力先  : ${LOG_FILE}"

        # コンテナ内で python -m uvicorn をフォアグラウンド実行するコマンド文字列を組み立てる
        # ※ uvicorn コマンドではなく python -m uvicorn を使う理由:
        #    uvicorn コマンドは起動時に logging.basicConfig() を呼び出してルートロガーに
        #    ハンドラを追加するため、アプリのログが二重出力になる。
        #    python -m uvicorn はそのステップをスキップするため二重出力が起きない。
        local inner_cmd="cd '${PROJECT_ROOT}' && python -m uvicorn ${APP_MODULE} --host ${HOST} --port ${PORT} --workers 1 --log-level ${LOG_LEVEL}"
        echo "  $inner_cmd"

        # nohup でコンテナごとバックグラウンド化する
        nohup "${VENV_COMMAND}" bash -c "${inner_cmd}" >> /dev/null 2>> "${UVICORN_LOG_FILE}" &

        local server_pid=$!
        echo "${server_pid}" > "${PID_FILE}"

        # uvicorn の起動完了を待つ（モデルロードがあるため長めに待つ）
        _wait_for_server "${server_pid}" "${SCRIPT_PATH}"
    fi
}

# コンテナ内（または仮想環境内）で uvicorn を nohup バックグラウンド起動する
# is_in_venv() が true のとき（すでにコンテナ内にいるとき）に使用する
_launch_uvicorn_direct() {
    local script_path="${1}"
    echo "  起動コマンド: python3 -m uvicorn ${APP_MODULE} --host ${HOST} --port ${PORT}"
    echo "  アプリログ  : ${LOG_FILE}"
    echo "  uvicornログ : ${UVICORN_LOG_FILE}"

    # nohup でバックグラウンド実行（ターミナルを閉じても継続稼働）
    nohup python3 -m uvicorn "${APP_MODULE}" \
        --host "${HOST}" \
        --port "${PORT}" \
        --workers 1 \
        --log-level "${LOG_LEVEL}" \
        >> /dev/null 2>> "${UVICORN_LOG_FILE}" &

    # バックグラウンドプロセスの PID を取得して PID ファイルに保存
    local server_pid=$!
    echo "${server_pid}" > "${PID_FILE}"

    # サーバーの起動完了を確認して結果を表示
    _wait_for_server "${server_pid}" "${script_path}"
}

# サーバーの起動完了を確認して結果を表示する共通関数
_wait_for_server() {
    local server_pid="${1}"
    local script_path="${2}"

    # uvicorn の起動完了を待つ
    # モデルロード（Qwen3-8B + ColQwen2.5）に数分かかる場合があるため
    # ポートが LISTEN 状態になるまで最大 300 秒（5 分）待つ
    local elapsed=0
    local max_wait=300
    echo -n "  サーバー起動待機中"
    while [ "${elapsed}" -lt "${max_wait}" ]; do
        # プロセスが死んでいたら即失敗
        if ! kill -0 "${server_pid}" 2>/dev/null; then
            echo ""
            echo -e "${RED}❌ サーバーの起動に失敗しました。ログを確認してください:${NC}"
            echo "   tail -n 50 ${LOG_FILE}"
            rm -f "${PID_FILE}"
            exit 1
        fi
        # ポートが LISTEN 状態になったら起動完了とみなす
        if ss -tlnp 2>/dev/null | grep -q ":${PORT} " || \
           lsof -iTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null | grep -q .; then
            break
        fi
        sleep 3
        elapsed=$((elapsed + 3))
        echo -n "."
    done
    echo ""

    if kill -0 "${server_pid}" 2>/dev/null; then
        # アクセス先の表示ホスト名を決定する（優先順位）:
        #   1. .env の SERVER_PUBLIC_HOST（明示指定が最優先）
        #   2. hostname -f の FQDN（DNS で解決できるとは限らないため注意）
        #   3. hostname -I の先頭 IP アドレス（フォールバック）
        local host_display
        if [ -n "${SERVER_PUBLIC_HOST:-}" ]; then
            host_display="${SERVER_PUBLIC_HOST}"
        else
            host_display="$(hostname -f 2>/dev/null || hostname -I | awk '{print $1}')"
        fi
        echo -e "${GREEN}✅ サーバー起動成功！${NC}"
        echo "   PID        : ${server_pid}"
        echo "   アクセス先 : http://${host_display}:${PORT}"
        echo "   Swagger UI : http://${host_display}:${PORT}/docs"
        echo "   ログ確認   : bash ${script_path} log"
    else
        echo -e "${RED}❌ サーバーの起動に失敗しました。ログを確認してください:${NC}"
        echo "   tail -n 50 ${LOG_FILE}"
        rm -f "${PID_FILE}"
        exit 1
    fi
}


# =============================================================================
# stop: サーバー停止
# =============================================================================
stop_server() {
    echo -e "${CYAN}=== FastAPI Server 停止 ===${NC}"

    if ! is_running; then
        echo -e "${YELLOW}⚠ サーバーは起動していません${NC}"
        # 残った PID ファイルがあれば削除
        rm -f "${PID_FILE}"
        exit 0
    fi

    # PID ファイルに保存されているのは sing-ai2_202605 コンテナの PID であり、
    # uvicorn プロセス本体ではない。SIGTERM を送っても uvicorn に届かないため、
    # ポートを Listen している uvicorn プロセスの PID を直接取得して停止する。
    local uvicorn_pid
    uvicorn_pid=$(lsof -ti tcp:"${PORT}" 2>/dev/null | head -1)

    if [ -z "${uvicorn_pid}" ]; then
        echo -e "${YELLOW}⚠ ポート ${PORT} で Listen しているプロセスが見つかりません${NC}"
        rm -f "${PID_FILE}"
        exit 0
    fi

    echo "  uvicorn PID ${uvicorn_pid} のプロセスを停止中..."

    # SIGTERM を送信してグレースフルシャットダウンを試みる
    kill -SIGTERM "${uvicorn_pid}" 2>/dev/null

    # 最大 15 秒待ってプロセスが終了するのを確認する
    local count=0
    while kill -0 "${uvicorn_pid}" 2>/dev/null && [ ${count} -lt 15 ]; do
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    echo ""

    # 15 秒経っても終了しない場合は SIGKILL で強制終了
    if kill -0 "${uvicorn_pid}" 2>/dev/null; then
        echo -e "${YELLOW}  グレースフルシャットダウンに失敗。強制終了します...${NC}"
        kill -SIGKILL "${uvicorn_pid}" 2>/dev/null
        sleep 1
    fi

    # コンテナプロセス（PID ファイルの PID）も念のため終了させる
    local container_pid
    container_pid=$(get_pid)
    if [ -n "${container_pid}" ] && kill -0 "${container_pid}" 2>/dev/null; then
        kill -SIGTERM "${container_pid}" 2>/dev/null
        sleep 1
    fi

    # PID ファイルを削除
    rm -f "${PID_FILE}"

    echo -e "${GREEN}✅ サーバーを停止しました${NC}"
}


# =============================================================================
# status: 稼働状況確認
# =============================================================================
show_status() {
    echo -e "${CYAN}=== FastAPI Server 稼働状況 ===${NC}"

    if is_running; then
        local pid
        pid=$(get_pid)
        echo -e "  状態    : ${GREEN}稼働中 (Running)${NC}"
        echo "  PID     : ${pid}"
        echo "  ポート  : ${PORT}"

        # ヘルスチェックエンドポイントへの接続確認（curl が使える場合）
        if command -v curl &>/dev/null; then
            echo ""
            echo "  ヘルスチェック結果:"
            curl -s --max-time 5 "http://localhost:${PORT}/health" \
                | python3 -m json.tool 2>/dev/null \
                || echo "  （ヘルスチェックに失敗しました。サーバーがまだ起動中かもしれません）"
        fi
    else
        echo -e "  状態    : ${RED}停止中 (Stopped)${NC}"
    fi
}


# =============================================================================
# log: ログのリアルタイム表示
# =============================================================================
show_log() {
    echo -e "${CYAN}=== FastAPI Server ログ（Ctrl+C で終了）===${NC}"

    if [ ! -f "${LOG_FILE}" ]; then
        echo -e "${YELLOW}⚠ ログファイルが見つかりません: ${LOG_FILE}${NC}"
        echo "  サーバーを起動してください: bash ${0} start"
        exit 1
    fi

    # tail -f でリアルタイムにログを表示する
    tail -f "${LOG_FILE}"
}


# =============================================================================
# usage: 使い方表示
# =============================================================================
show_usage() {
    echo ""
    echo "使い方:"
    echo "  bash $(basename "${0}") <コマンド>"
    echo ""
    echo "コマンド:"
    echo "  start    サーバーを起動します"
    echo "  stop     サーバーを停止します"
    echo "  status   稼働状況を表示します"
    echo "  log      直近のログをリアルタイムで表示します（Ctrl+C で終了）"
    echo ""
    echo "例:"
    echo "  bash $(basename "${0}") start"
    echo "  bash $(basename "${0}") status"
    echo "  bash $(basename "${0}") log"
    echo ""
}


# =============================================================================
# メイン処理: コマンドの振り分け
# =============================================================================
case "${1}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    status)
        show_status
        ;;
    log)
        show_log
        ;;
    *)
        # 上記以外のコマンドまたは引数なしの場合は usage を表示
        show_usage
        exit 1
        ;;
esac
