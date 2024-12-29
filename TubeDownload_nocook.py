import yt_dlp
import os
import streamlit as st

# Функция для получения доступных форматов (включая аудио и видео)
def get_available_formats(url):
    ydl_opts = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
    
    formats = info_dict.get('formats', [])
    video_formats = []
    audio_formats = []

    # Разделение видео и аудио форматов
    for f in formats:
        if f.get('height') is not None and f.get('ext') == 'mp4' and f.get('filesize') is not None:
            if f['height'] >= 720:
                video_formats.append(f)
        if f.get('acodec') == 'mp4a.40.2' and f.get('ext') == 'm4a' and f.get('filesize') is not None:
            audio_formats.append(f)

    return video_formats, audio_formats

# Колбэк для отображения прогресса
def progress_hook(d):
    if d['status'] == 'downloading':
        # Убираем лишние escape-коды
        percent = d.get('_percent_str', '').replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip()
        speed = d.get('_speed_str', '').replace('\x1b[0;32m', '').replace('\x1b[0m', '').strip()
        eta = d.get('_eta_str', '').replace('\x1b[0;33m', '').replace('\x1b[0m', '').strip()

        # Вычисляем прогресс для шкалы
        progress = float(percent.strip('%')) / 100.0 if '%' in percent else 0.0

        # Обновляем элементы интерфейса
        st.session_state.progress_bar.progress(progress)
        st.session_state.status_text.text(f"Скачано: {percent} | Скорость: {speed} | Оставшееся время: {eta}")


# Основная функция для скачивания видео и аудио
def download_video(url, video_format, audio_format, download_dir):
    ydl_opts = {
        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
        'format': f'{video_format["format_id"]}+{audio_format["format_id"]}',  # Скачиваем и видео, и аудио
        'merge_output_format': 'mp4',  # Конвертировать в mp4
        'progress_hooks': [progress_hook],  # Подключение колбэка
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            st.success(f"Видео успешно загружено в {download_dir}")
        except Exception as e:
            st.error(f"Ошибка при загрузке: {e}")

# Интерфейс Streamlit
def main():
    st.title("Загрузчик видео с YouTube")

    # Ввод URL
    url = st.text_input("Введите URL видео с YouTube:")

    if url:

        # Получение доступных форматов
        video_formats, audio_formats = get_available_formats(url)

        if video_formats and audio_formats:
            st.subheader("Доступные форматы видео:")

            # Создание списка доступных видео форматов
            format_options = []
            for video in video_formats:
                # Для каждого видео находим лучший аудиоформат и считаем общий размер
                best_audio_format = max(audio_formats, key=lambda f: f['filesize'])
                total_size = video['filesize'] + best_audio_format['filesize']
                format_options.append({
                    'video': video,
                    'audio': best_audio_format,
                    'total_size': total_size,
                    'display': f"{video['height']}p - {video['ext']} - {total_size/(1024*1024):.2f} MB"
                })

            selected_format_index = st.selectbox("Выберите качество видео", [f['display'] for f in format_options])

            # Получаем выбранный формат
            selected_format = format_options[[f['display'] for f in format_options].index(selected_format_index)]

            # Выбор директории для сохранения
            download_dir = os.path.dirname(os.path.abspath(__file__))

            # Кнопка для начала загрузки
            if st.button("Скачать видео"):
                # Создание директории, если её нет
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)

                # Перед началом загрузки, инициализируем элементы интерфейса
                if 'progress_bar' not in st.session_state:
                    st.session_state.progress_bar = st.progress(0)
                    st.session_state.status_text = st.empty()

                with st.spinner("Скачивание видео... Это может занять некоторое время"):
                    download_video(url, selected_format['video'], selected_format['audio'], download_dir)
        else:
            st.error("Не удалось получить доступные форматы для данного видео.")
    else:
        st.warning("Введите URL видео для продолжения.")

if __name__ == "__main__":
    main()