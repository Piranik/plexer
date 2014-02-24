#!/usr/bin/python

import sys
import re
import argparse
from os import listdir, mkdir, rename
from os.path import isfile, isdir, splitext, basename, sep

MEDIA_EXTENSIONS = ['.mp4', '.avi', '.mkv', '.mpeg', '.mpg']
MATCHING_REGEX = r'([a-zA-Z0-9\\. ]+)((S|s)([0-9]{1,2}))((E|e)([0-9]{1,2}))'
DESCRIPTION = 'organize downloaded tv series into plex compatible structures'


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('source', help='source directory containing one or more series')
    parser.add_argument('target', help='target directory for structure output')
    parser.add_argument('--test', help='show the processed structure but do not actually move files',
                        action='store_true')
    args = parser.parse_args()

    if not args.source or not args.target:
        parser.print_help()
        exit(-1)

    series_list = {}

    for entry in find_media_files(args.source):
        file_name = basename(entry)
        matches = re.search(MATCHING_REGEX, file_name)
        if matches:
            series_name = matches.group(1).replace('.', ' ').strip().title()
            season_number = int(matches.group(4))
            episode_number = int(matches.group(7))

            series = series_list.get(series_name, Series(series_name))
            season = series.get_season(season_number)
            season.put_episode(episode_number, SeriesEpisode(episode_number, entry))
            series.put_season(season_number, season)
            series_list[series_name] = series

    for series_name, series in series_list.items():
        print series_name
        for season_number, season in series.seasons.items():
            sys.stdout.write('\tSeason %02d:' % season_number)
            sys.stdout.write('  ')
            for episode_number, episode in season.episodes.items():
                sys.stdout.write('%d  ' % episode_number)

            sys.stdout.write('\n\n')

    print 'Structured %d total series ' % len(series_list)

    if not args.test:
        print 'moving files to target directory %s' % args.target
        for series_name, series in series_list.items():
            mkdir(args.target + sep + series_name)
            for season_number, season in series.seasons.items():
                season_path = args.target + sep + series_name + sep +'Season %02d' % season_number
                mkdir(season_path)
                for episode_number, episode in season.episodes.items():
                    file_extension = splitext(episode.path)[1]
                    episode_fmt = '%s - s%02de%02d%s' % (series_name, season_number, episode_number, file_extension)
                    episode_path = season_path + sep + episode_fmt
                    rename(episode.path, episode_path)


class Series:

    def __init__(self, name):
        self.name = name
        self.seasons = {}

    def get_season(self, season_number):
        return self.seasons.get(season_number, SeriesSeason(season_number))

    def put_season(self, season_number, season):
        self.seasons[season_number] = season


class SeriesSeason:

    def __init__(self, number):
        self.number = number
        self.episodes = {}

    def get_episode(self, episode_number):
        return self.episodes.get(episode_number, SeriesEpisode(episode_number))

    def put_episode(self, episode_number, episode):
        self.episodes[episode_number] = episode


class SeriesEpisode:

    def __init__(self, number, path):
        self.number = number
        self.path = path


def find_media_files(root_dir):
    for entry in listdir(root_dir):
        entry_path = root_dir + entry
        if isdir(entry_path):
            find_media_files(root_dir + entry)

        elif isfile(entry_path):
            name, extension = splitext(entry_path)
            if extension in MEDIA_EXTENSIONS:
                yield entry_path


if __name__ == "__main__":
    main()

