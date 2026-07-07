
set -e
cd /var/www/my_site_prod_repo_new
echo '=== ALL FILE/IMAGE FIELDS ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "import json; from pathlib import Path; from django.apps import apps; from django.conf import settings; from django.db.models.fields.files import FileField; root=Path(settings.MEDIA_ROOT); rows=[]
for model in apps.get_models():
    fields=[f for f in model._meta.fields if isinstance(f, FileField)]
    if not fields: continue
    for obj in model.objects.all().order_by('pk'):
        for f in fields:
            val=getattr(obj,f.name)
            name=getattr(val,'name','') or ''
            if name:
                rows.append({'model':model._meta.label,'pk':obj.pk,'field':f.name,'path':name,'exists':(root/name).exists(),'url':getattr(val,'url',None)})
print(json.dumps(rows,ensure_ascii=False,indent=2))"
echo '=== HOME PAGE MEDIA/STATIC REFS ==='
curl -k -sS https://rgavanp.kdns.fr/ | grep -Eo '(src|href)="[^"]+"' | sed -n '1,200p' || true
echo '=== BLOG PAGE MEDIA REFS ==='
curl -k -sS https://rgavanp.kdns.fr/blog/ | grep -Eo '(src|href)="[^"]+"' | sed -n '1,200p' || true
echo '=== TEMPLATES MEDIA STATIC IMAGE REFS ==='
docker exec my_site_prod_repo-web-1 sh -lc "grep -RIn \"media/\|static .*jpg\|static .*png\|img src\|cover_image\|image.url\|audio_file\" /code/*/templates /code/templates 2>/dev/null | head -n 200"
echo '=== IMAGE APP MODELS ==='
docker exec my_site_prod_repo-web-1 sh -lc "sed -n '1,220p' /code/images/models.py; echo ---; grep -RIn \"ImagePost\|image\" /code/images /code/*/templates 2>/dev/null | head -n 120"
