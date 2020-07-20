import glob
import guru

def download_file(url, filename):
  if "tettra-production.s3" in url:
    status_code, file_size = guru.download_file(url, filename)
    return status_code < 400

if __name__ == "__main__":
  g = guru.Guru()
  sync = g.sync(id="tettra", verbose=True)

  for filename in glob.glob("/Users/rmiller/Downloads/tettra/*.html")[0:15]:
    shortname = filename[filename.rfind("/")+1:]
    doc = guru.load_html(filename)
    title = doc.select("title")[0].text
    # todo: convert links like https://app.tettra.co/teams/palmetto-team/pages/establishing-your-rocks-your-specific-90-day-goals
    #       to reference local html pages.
    content = str(doc.select("body")[0])
    sync.node(
      id=shortname,
      url=filename,
      title=title,
      content=content
    )

  sync.zip(download_func=download_file)
  sync.print_tree()
  sync.view_in_browser()
