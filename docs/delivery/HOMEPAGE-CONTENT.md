# ELASI — Homepage content (Delivery 05.9)

This is a small, structured homepage editor in **Django Admin**, not a visual drag-and-drop builder.

1. Apply the Django migration (`apps.core.0001_homepage_content`) to the approved environment.
2. In `/admin/`, open **محتوای صفحه اصلی** and create the single homepage record.
3. Edit hero copy, optional hero photograph + descriptive alt text, story and closing text.
4. Publish by checking **منتشر شده**; saving an unpublished record leaves the existing frontend fallback visible.
5. To unpublish, uncheck the same box. Only published fields are available at `GET /api/v1/homepage/`. If no published record exists, the endpoint returns `204 No Content` and the storefront displays its existing fallback.

The homepage keeps its existing product-based visual if no new hero photograph is uploaded. A CMS photo replaces the automatic catalog product hero and does not display the product overlay. CTA links are fixed (`/shop`, `/about`) to avoid sending customers to arbitrary external URLs.

Access follows Django Admin model permissions. Only designated staff with `core.add_homepagecontent` / `core.change_homepagecontent` can maintain it. An editor cannot delete the only record.

**Operational caution:** Uploaded images use Django's configured media storage. Production must have persistent object storage or equivalent; a Render ephemeral filesystem is **not** adequate for merchant-uploaded content. This delivery does not configure that storage or establish the client's final imagery.
