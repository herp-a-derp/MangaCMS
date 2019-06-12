
import inspect
import MangaCMSOld.lib.logSetup
MangaCMSOld.lib.logSetup.initLogging()

import MangaCMSOld.cleaner.processDownload
import MangaCMSOld.DbBase

import MangaCMSOld.ScrapePlugins.H.ASMHentaiLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.H.ASMHentaiLoader.DbLoader
import MangaCMSOld.ScrapePlugins.H.DjMoeLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.H.DjMoeLoader.DbLoader
import MangaCMSOld.ScrapePlugins.H.DoujinOnlineLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.H.DoujinOnlineLoader.DbLoader
import MangaCMSOld.ScrapePlugins.H.HBrowseLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.H.HBrowseLoader.DbLoader
import MangaCMSOld.ScrapePlugins.H.Hentai2Read.ContentLoader
import MangaCMSOld.ScrapePlugins.H.Hentai2Read.DbLoader
import MangaCMSOld.ScrapePlugins.H.HitomiLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.H.HitomiLoader.DbLoader
import MangaCMSOld.ScrapePlugins.H.NHentaiLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.H.NHentaiLoader.DbLoader
import MangaCMSOld.ScrapePlugins.H.PururinLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.H.PururinLoader.DbLoader
import MangaCMSOld.ScrapePlugins.H.SadPandaLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.H.SadPandaLoader.DbLoader
import MangaCMSOld.ScrapePlugins.H.TsuminoLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.H.TsuminoLoader.DbLoader
import MangaCMSOld.ScrapePlugins.M.BooksMadokami.ContentLoader
import MangaCMSOld.ScrapePlugins.M.BooksMadokami.DbLoader
import MangaCMSOld.ScrapePlugins.M.Crunchyroll.ContentLoader
import MangaCMSOld.ScrapePlugins.M.Crunchyroll.DbLoader
import MangaCMSOld.ScrapePlugins.M.CxLoader.contentLoader
import MangaCMSOld.ScrapePlugins.M.CxLoader.dbLoader
import MangaCMSOld.ScrapePlugins.M.DynastyLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.M.DynastyLoader.FeedLoader
import MangaCMSOld.ScrapePlugins.M.FoolSlide.VortexLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.M.FoolSlide.VortexLoader.FeedLoader
import MangaCMSOld.ScrapePlugins.M.GameOfScanlationLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.M.GameOfScanlationLoader.FeedLoader
import MangaCMSOld.ScrapePlugins.M.Kawaii.ContentLoader
import MangaCMSOld.ScrapePlugins.M.Kawaii.FeedLoader
import MangaCMSOld.ScrapePlugins.M.KissLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.M.KissLoader.FeedLoader
import MangaCMSOld.ScrapePlugins.M.MangaBox.Loader
import MangaCMSOld.ScrapePlugins.M.MangaHere.ContentLoader
import MangaCMSOld.ScrapePlugins.M.MangaHere.FeedLoader
import MangaCMSOld.ScrapePlugins.M.MangaMadokami.ContentLoader
import MangaCMSOld.ScrapePlugins.M.MangaMadokami.FeedLoader
import MangaCMSOld.ScrapePlugins.M.MangaStreamLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.M.MangaStreamLoader.FeedLoader
import MangaCMSOld.ScrapePlugins.M.McLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.M.McLoader.FeedLoader
import MangaCMSOld.ScrapePlugins.M.MerakiScans.ContentLoader
import MangaCMSOld.ScrapePlugins.M.MerakiScans.FeedLoader
import MangaCMSOld.ScrapePlugins.M.SurasPlace.ContentLoader
import MangaCMSOld.ScrapePlugins.M.SurasPlace.FeedLoader
import MangaCMSOld.ScrapePlugins.M.WebtoonLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.M.WebtoonLoader.FeedLoader
import MangaCMSOld.ScrapePlugins.M.WebtoonsReader.ContentLoader
import MangaCMSOld.ScrapePlugins.M.WebtoonsReader.FeedLoader
import MangaCMSOld.ScrapePlugins.M.YoMangaLoader.Loader
import MangaCMSOld.ScrapePlugins.M.ZenonLoader.ContentLoader
import MangaCMSOld.ScrapePlugins.M.ZenonLoader.FeedLoader

files = [
	MangaCMSOld.ScrapePlugins.H.ASMHentaiLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.H.ASMHentaiLoader.DbLoader,
	MangaCMSOld.ScrapePlugins.H.DjMoeLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.H.DjMoeLoader.DbLoader,
	MangaCMSOld.ScrapePlugins.H.DoujinOnlineLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.H.DoujinOnlineLoader.DbLoader,
	MangaCMSOld.ScrapePlugins.H.HBrowseLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.H.HBrowseLoader.DbLoader,
	MangaCMSOld.ScrapePlugins.H.Hentai2Read.ContentLoader,
	MangaCMSOld.ScrapePlugins.H.Hentai2Read.DbLoader,
	MangaCMSOld.ScrapePlugins.H.HitomiLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.H.HitomiLoader.DbLoader,
	MangaCMSOld.ScrapePlugins.H.NHentaiLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.H.NHentaiLoader.DbLoader,
	MangaCMSOld.ScrapePlugins.H.PururinLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.H.PururinLoader.DbLoader,
	MangaCMSOld.ScrapePlugins.H.SadPandaLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.H.SadPandaLoader.DbLoader,
	MangaCMSOld.ScrapePlugins.H.TsuminoLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.H.TsuminoLoader.DbLoader,
	MangaCMSOld.ScrapePlugins.M.BooksMadokami.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.BooksMadokami.DbLoader,
	MangaCMSOld.ScrapePlugins.M.Crunchyroll.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.Crunchyroll.DbLoader,
	MangaCMSOld.ScrapePlugins.M.CxLoader.contentLoader,
	MangaCMSOld.ScrapePlugins.M.CxLoader.dbLoader,
	MangaCMSOld.ScrapePlugins.M.DynastyLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.DynastyLoader.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.VortexLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.VortexLoader.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.GameOfScanlationLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.GameOfScanlationLoader.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.Kawaii.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.Kawaii.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.KissLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.KissLoader.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.MangaBox.Loader,
	MangaCMSOld.ScrapePlugins.M.MangaHere.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.MangaHere.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.MangaMadokami.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.MangaMadokami.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.MangaStreamLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.MangaStreamLoader.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.McLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.McLoader.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.MerakiScans.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.MerakiScans.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.SurasPlace.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.SurasPlace.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.WebtoonLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.WebtoonLoader.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.WebtoonsReader.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.WebtoonsReader.FeedLoader,
	MangaCMSOld.ScrapePlugins.M.YoMangaLoader.Loader,
	MangaCMSOld.ScrapePlugins.M.ZenonLoader.ContentLoader,
	MangaCMSOld.ScrapePlugins.M.ZenonLoader.FeedLoader,
]

def go():
	print(MangaCMSOld.cleaner.processDownload)
	for code_file in files:
		# print(code_file)
		classes = inspect.getmembers(code_file, inspect.isclass)
		for class_name, class_def in classes:
			# print(class_def)
			if issubclass(class_def, MangaCMSOld.DbBase.DbBase):
				print("class:", class_def)
				instance = class_def()
				cur = instance.get_cursor()
				instance.release_cursor(cur)

if __name__ == '__main__':
	go()
