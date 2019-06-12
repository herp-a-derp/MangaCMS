
from sqlalchemy.dialects.postgresql import ENUM

dlstate_enum   = ENUM('new', 'fetching', 'processing', 'complete', 'error', 'removed', 'disabled', 'upload', 'missing', name='dlstate_enum')
dir_type       = ENUM('had_dir', 'created_dir', 'unknown', name='dirtype_enum')
file_type      = ENUM('manga', 'hentai', 'unknown', name='filetype_enum')

