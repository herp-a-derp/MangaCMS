
import abc
import statsd

import settings

class MonitorMixin(metaclass=abc.ABCMeta):

	@abc.abstractmethod
	def logger_path(self):
		return None

	@abc.abstractmethod
	def plugin_name(self):
		return None
	@abc.abstractmethod
	def plugin_type(self):
		return None

	@abc.abstractmethod
	def is_manga(self):
		return None

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


		if settings.GRAPHITE_DB_IP:
			assert self.plugin_name
			assert self.logger_path

			prefix_str = 'MangaCMS.Scrapers.{scrape_type}.{plugin_name}.{plugin_type}.{logger_path}'.format(
								scrape_type = "Manga" if self.is_manga else "Hentai",
								plugin_type = self.plugin_type,
								plugin_name  = self.plugin_name.replace(".", "_").replace("-", "_").replace(" ", "_"),
								logger_path = self.logger_path.replace("-", "_").replace(" ", "_"),
							)

			print("Graphite prefix path: '%s'" % prefix_str)

			self.mon_con = statsd.StatsClient(
					host = settings.GRAPHITE_DB_IP,
					port = 8125,
					prefix = prefix_str
					)
		else:
			self.mon_con = None

