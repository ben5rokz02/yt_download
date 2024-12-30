import yt_dlp
import tempfile
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

# Основная функция для скачивания видео и аудио
def download_video(url, video_format, audio_format):
    ydl_opts = {
        'format': f'{video_format["format_id"]}+{audio_format["format_id"]}',  # Скачиваем и видео, и аудио
        'merge_output_format': 'mp4',  # Конвертировать в mp4
    }
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmpfile:
        ydl_opts['outtmpl'] = tmpfile.name  # Сохраняем файл во временную директорию
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
                return tmpfile.name  # Возвращаем путь к временно сохраненному файлу
            except Exception as e:
                st.error(f"Ошибка при загрузке: {e}")
                return None

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

            # Кнопка для начала загрузки
            if st.button("Скачать видео"):
                with st.spinner("Скачивание видео... Это может занять некоторое время"):
                    # Скачиваем видео во временный файл
                    tmp_file_path = download_video(url, selected_format['video'], selected_format['audio'])
                    
                    if tmp_file_path:
                        # Открываем временный файл для загрузки через браузер
                        with open(tmp_file_path, "rb") as tmp_file:
                            st.download_button(
                                label="Скачать видео",
                                data=tmp_file,
                                file_name=f"{selected_format['video']['height']}p_video.mp4",
                                mime="video/mp4"
                            )
        else:
            st.error("Не удалось получить доступные форматы для данного видео.")
    else:
        st.warning("Введите URL видео для продолжения.")

if __name__ == "__main__":
    main()
