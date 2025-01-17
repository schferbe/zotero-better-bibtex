from steps.zotero import Zotero
from behave.contrib.scenario_autoretry import patch_scenario_with_autoretry
import re
from contextlib import contextmanager
import urllib.request
from munch import *
import os
import steps.utils as utils
import sys

@contextmanager
def value_tag(tag):
    name = tag
    value = None

    if '=' in tag:
      s = tag.split('=', 1)
      name = s[0]
      try:
        value = int(s[1])
      except:
        raise ValueError(f'{tag} must specify a valid integer')
    elif ':' in tag:
      s = tag.split(':', 1)
      name = s[0]
      value = s[1]
      if len(value) == 0: raise ValueError(f'{tag} must specify a valid string')

    yield (name, value)

def before_feature(context, feature):
  for scenario in feature.walk_scenarios():
    retries = 0
    for tag in scenario.effective_tags:
      with value_tag(tag) as (tag, value):
        if tag == 'retry':
          retries = max(retries, 1)
        elif tag == 'retries':
          value = value or 0
          if value == 0: raise ValueError(f'{value} is not a valid number of retries')
          retries = max(retries, value)

    if retries > 0:
      patch_scenario_with_autoretry(scenario, max_attempts=retries + 1)

def before_all(context):
  context.zotero = Zotero(context.config.userdata)
  # test whether the existing references, if any, have gotten a cite key
  context.zotero.export_library(translator = 'Better BibTeX')

def before_scenario(context, scenario):
  client = [tag for tag in scenario.effective_tags if tag in ['jurism', 'zotero']]
  if len(client) > 0 and not context.zotero.client in client:
    scenario.skip(f'{str(client)}-specific scenario skipped for {context.zotero.client}')
    return

  context.zotero.reset()
  context.displayOptions = {}
  context.selected = []
  context.imported = None
  context.picked = []

  context.timeout = 60
  for tag in scenario.effective_tags:
    with value_tag(tag) as (tag, value):
      if tag == 'nightly':
        context.timeout = max(context.timeout, 300)
      elif tag == 'timeout':
        value = value or 0
        assert value > 0, f'{value} is not a valid timeout'
        context.timeout = max(context.timeout, value)
  context.zotero.config.timeout = context.timeout
