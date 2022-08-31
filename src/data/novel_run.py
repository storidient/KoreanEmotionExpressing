from src.data.novel_preprocess import *

dir_path = '/content/drive/MyDrive/WebNovel/한국 소설/'

for (root, directories, files) in os.walk(dir_path):
    for file in files:
        if '.xlsx' in file:

          file_path = os.path.join(root, file)
          data = pd.read_excel(file_path, index_col=0)
          refined_data = pd.DataFrame(refine_enter(data))
          new_path = os.path.join('/content/drive/MyDrive/WebNovel/', 'refined_text', file)
          refined_data.to_excel('/content/drive/MyDrive/WebNovel/' + 'refined_text/' + file)
