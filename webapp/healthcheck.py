# -*- coding: utf-8 -*-
from django.http import HttpResponse


def healthcheck_status(request):
    return HttpResponse("OK")
