import os
import random
import sqlite3
import threading
import time
import zipfile
import requests
import telebot

# Aapke saare 18 verified bot tokens ki list
TOKENS = [
    "8902637263:AAEfkuzqnCK-gEkKOS4d8jBBhzxMJp9ybdo",  # Bot 1 (Primary - Commands receive karega)
    "8645394403:AAEPDtMkvi12pu978Lww9q5SN4d6e5kCmgg",  # Bot 2
    "8947614914:AAFIInooiRZJ8Pl6mIT0Qmu018-gYCLAMJk",  # Bot 3
    "8951573997:AAGRT6Ty0Fk_dqOV7bBW8VR-41hFiJyH45E",  # Bot 4
    "8859672236:AAGBxZaMsPoL8LmBFQVrF1548utOk7WeDyA",  # Bot 5
    "8938269240:AAHm1kp_oWAqMt0S2PWgx6Fz0mObVG-nSFE",  # Bot 6
    "8496369381:AAE_92xDeAyUu6viBP2X8lsyHUYTqqj7a_U",  # Bot 7
    "8672201515:AAEC_WMDjltgFT9_eBpYrvsTfK8ApxbdK9s",  # Bot 8
    "9240565924:AAGyeAQQl3aEYLokeEWw-O25ygg2Lqjfliw",  # Bot 9
    "9161460043:AAE11dcD361LQcimSSZFE9OK9CJ-zxBMarA",  # Bot 10
    "9019490232:AAHYLzYbOXvTjahSlxic1e80we3F2zW6FWs",  # Bot 11
    "9158410901:AAFfd6AlVnRTquiUvx-RhwRZpeETHc9GtFc",  # Bot 12
    "9100820559:AAHfOf8FEEZ2GMPAemHuxpwrxxKUkbzM-6k",  # Bot 13
    "9197217859:AAEQIvDFtgi_o3bsLMcLJJs-ZdFFIT8lofM",  # Bot 14
    "9277982939:AAET6hReyDsRx5jwTuw7waUPstIq996zdY4",  # Bot 15
    "9209665024:AAHwqqYt8gDv6JN1sPGQfMdXcJR5SsbOfM0",  # Bot 16
    "9117792998:AAGScydqQFb6VEm3ouNVc1IbZqg00F4_2OY",  # Bot 17
    "9068118181:AAHiATVT785Ih4j7CSZLcEVS_reptVOnIXU",  # Bot 18
]

# Primary bot token for receiving commands and sending files
PRIMARY_TOKEN = TOKENS[0]
bot = telebot.TeleBot(PRIMARY_TOKEN)

user_session = {}
db_lock = threading.Lock()  # SQLite database safety lock


@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "🤖 **Distributed 18-Worker Bot Active!**\n\nCommand use karein:\n`/getdb"
      " <API_URL>`",
      parse_mode="Markdown",
  )


@bot.message_handler(commands=["getdb"])
def ask_mode(message):
  try:
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
      bot.reply_to(
          message,
          "❌ Kripya API URL bhi dein.\nExample: `/getdb"
          " https://admin.gbssystems.com/public/gateway/apiv1/api.php?key=9NXZC&cmd=number&query=`",
          parse_mode="Markdown",
      )
      return

    user_session[message.chat.id] = {"url": parts[1].strip()}

    msg = bot.reply_to(
        message,
        "📊 **Mode Select Karein:**\n1️⃣ Agar **500** ya koi fix number ka data"
        " chahiye, toh wo number likhein (jaise `500`).\n2️⃣ Agar **Unlimited**"
        " chahiye, toh `all` likhein.",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(msg, start_fetching_process)

  except Exception as e:
    bot.reply_to(message, f"❌ Error: {str(e)}")


def start_fetching_process(message):
  try:
    chat_id = message.chat.id
    user_input = message.text.strip().lower()

    if chat_id not in user_session:
      bot.reply_to(
          message, "❌ Session expire ho gaya. Dobara `/getdb <URL>` se shuru karein."
      )
      return

    base_url = user_session[chat_id]["url"]

    if user_input == "all":
      limit = None
      progress_msg = bot.reply_to(
          message,
          "⚡ **Distributed Safe Mode Activated (18 Workers)!**\n📥 Total Records Found: 0",
          parse_mode="Markdown",
      )
    else:
      try:
        limit = int(user_input)
        progress_msg = bot.reply_to(
            message,
            f"⚡ **{limit} Numbers Safe Mode Activated (18 Workers)!**\n0 / {limit}"
            " processed.",
            parse_mode="Markdown",
        )
      except ValueError:
        bot.reply_to(
            message,
            "❌ Kripya valid number (jaise `500`) ya `all` likhein.",
        )
        return

    db_name = "safe_records.db"
    if os.path.exists(db_name):
      os.remove(db_name)

    # Database initialization
    conn = sqlite3.connect(db_name, check_same_thread=False)
    cursor = conn.cursor()
    table_created = [False]

    total_fetched = {"count": 0}
    start_number = 9093614200
    state = {"i": 0, "consecutive_empty": 0}

    def worker_task(token):
      while True:
        with db_lock:
          if limit is not None and state["i"] >= limit:
            break
          if limit is None and state["consecutive_empty"] >= 50:
            break

          curr_idx = state["i"]
          state["i"] += 1

        current_number = start_number + curr_idx

        if base_url.endswith("="):
          api_url = f"{base_url}{current_number}"
        elif "?" in base_url:
          api_url = f"{base_url}&query={current_number}"
        else:
          api_url = f"{base_url}?query={current_number}"

        try:
          # Safe random delay taaki IP / API block na ho
          time.sleep(random.uniform(1.5, 3.0))

          response = requests.get(api_url, timeout=4)
          if response.status_code == 200:
            try:
              res_data = response.json()
            except:
              res_data = None

            if res_data:
              records = []
              if isinstance(res_data, list):
                records = res_data
              elif isinstance(res_data, dict):
                records = (
                    res_data.get("results")
                    or res_data.get("data")
                    or res_data.get("record")
                    or [res_data]
                )

              if records:
                with db_lock:
                  if not table_created[0]:
                    sample_item = (
                        records[0]
                        if isinstance(records[0], dict)
                        else {"content": str(records[0])}
                    )
                    keys = list(sample_item.keys())
                    columns_def = ", ".join([f'"{key}" TEXT' for key in keys])
                    cursor.execute(
                        f"CREATE TABLE IF NOT EXISTS all_records ({columns_def})"
                    )
                    conn.commit()
                    table_created[0] = True

                  for item in records:
                    if isinstance(item, dict):
                      keys = list(item.keys())
                      values = [str(item.get(key, "")) for key in keys]
                      placeholders = ", ".join(["?" for _ in keys])
                      cursor.execute(
                          f"INSERT INTO all_records VALUES ({placeholders})",
                          values,
                      )
                    else:
                      cursor.execute(
                          "INSERT INTO all_records VALUES (?)", (str(item),)
                      )
                  conn.commit()
                  total_fetched["count"] += (
                      len(records) if isinstance(records, list) else 1
                  )
                  state["consecutive_empty"] = 0
              else:
                with db_lock:
                  state["consecutive_empty"] += 1
            else:
              with db_lock:
                state["consecutive_empty"] += 1
          elif response.status_code == 429:
            # Rate limit hit hone par thoda lamba break
            time.sleep(15)
          else:
            with db_lock:
              state["consecutive_empty"] += 1

        except:
          with db_lock:
            state["consecutive_empty"] += 1

    # Multi-worker threads chalana (18 tokens ke sath parallel processing)
    threads = []
    for token in TOKENS:
      t = threading.Thread(target=worker_task, args=(token,))
      t.start()
      threads.append(t)

    # Live progress update loop
    while any(t.is_alive() for t in threads):
      time.sleep(3)
      try:
        if limit is not None:
          text_update = (
              f"⏳ **Distributed Fetching (18 Workers)...**\n"
              f"✅ Done: {state['i']} / {limit}\n"
              f"📥 Found Records: {total_fetched['count']}"
          )
        else:
          text_update = (
              f"⏳ **Unlimited Distributed Fetching (18 Workers)...**\n"
              f"🔢 Checked Numbers: {state['i']}\n"
              f"📥 Found Records: {total_fetched['count']}"
          )
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_msg.message_id,
            text=text_update,
            parse_mode="Markdown",
        )
      except:
        pass

    for t in threads:
      t.join()

    conn.close()

    # Final ZIP File Sending
    if os.path.exists(db_name) and os.path.getsize(db_name) > 0:
      file_size_mb = os.path.getsize(db_name) / (1024 * 1024)
      file_to_send = db_name

      # ZIP compression
      zip_name = "safe_records.zip"
      with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(db_name, os.path.basename(db_name))
      file_to_send = zip_name
      zip_size_mb = os.path.getsize(zip_name) / (1024 * 1024)
      caption = f"🗜️ **Compressed ZIP Ready!**\n📊 Total Records: {total_fetched['count']}\n📦 Size: {zip_size_mb:.2f} MB"

      bot.edit_message_text(
          chat_id=chat_id,
          message_id=progress_msg.message_id,
          text="✅ **Complete! ZIP file bheji ja rahi hai...**",
          parse_mode="Markdown",
      )

      with open(file_to_send, "rb") as f:
        bot.send_document(
            message.chat.id, f, caption=caption, parse_mode="Markdown"
        )

      if os.path.exists(db_name):
        os.remove(db_name)
      if os.path.exists(zip_name):
        os.remove(zip_name)
    else:
      bot.edit_message_text(
          chat_id=chat_id,
          message_id=progress_msg.message_id,
          text="❌ Koi valid data nahi mila.",
          parse_mode="Markdown",
      )

  except Exception as e:
    bot.reply_to(message, f"❌ Error: {str(e)}")


if __name__ == "__main__":
  print("🤖 18-Worker Distributed Bot started successfully...")
  bot.infinity_polling()
