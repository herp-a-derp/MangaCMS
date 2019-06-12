



import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.CanisMajorRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.ChibiMangaRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.DokiRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.GoMangaCoRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.IlluminatiMangaRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.JaptemMangaRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.MangatopiaRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.RoseliaRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.S2Run
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.SenseRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.ShoujoSenseRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.TripleSevenRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.TwistedHelRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.VortexRun
import utilities.testBase as tb

modules = [
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.CanisMajorRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.ChibiMangaRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.DokiRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.GoMangaCoRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.IlluminatiMangaRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.JaptemMangaRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.MangatopiaRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.RoseliaRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.S2Run.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.SenseRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.ShoujoSenseRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.TripleSevenRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.TwistedHelRun.Runner,
	MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.VortexRun.Runner,
]

if __name__ == '__main__':

	with tb.testSetup():
		for module in modules:
			mod = module()
			mod.go()

