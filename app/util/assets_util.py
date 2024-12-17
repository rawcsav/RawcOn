from flask_assets import Bundle


def compile_static_assets(assets):
    common_style_bundle = Bundle("src/common.css", filters="cssmin", output="dist/css/common.css")
    auth_style_bundle = Bundle("auth/landing.css", filters="cssmin", output="dist/css/auth.css")
    user_style_bundle = Bundle("user/profile.css", filters="cssmin", output="dist/css/user.css")
    playlist_style_bundle = Bundle("playlist/playlist.css", filters="cssmin", output="dist/css/playlist.css")
    recs_style_bundle = Bundle("recs/recs.css", filters="cssmin", output="dist/css/recs.css")

    assets.register("common_style_bundle", common_style_bundle)
    assets.register("auth_style_bundle", auth_style_bundle)
    assets.register("user_style_bundle", user_style_bundle)
    assets.register("playlist_style_bundle", playlist_style_bundle)
    assets.register("recs_style_bundle", recs_style_bundle)

    common_js_bundle = Bundle("src/common.js", filters="jsmin", output="dist/js/common.js")
    auth_js_bundle = Bundle("auth/landing.js", filters="jsmin", output="dist/js/auth.js")
    user_js_bundle = Bundle("user/profile.js", filters="jsmin", output="dist/js/user.js")
    playlist_js_bundle = Bundle("playlist/playlist.js", filters="jsmin", output="dist/js/playlist.js")
    recs_js_bundle = Bundle("recs/recs.js", filters="jsmin", output="dist/js/recs.js")

    assets.register("common_js_bundle", common_js_bundle)
    assets.register("auth_js_bundle", auth_js_bundle)
    assets.register("user_js_bundle", user_js_bundle)
    assets.register("playlist_js_bundle", playlist_js_bundle)
    assets.register("recs_js_bundle", recs_js_bundle)

    if assets.config["FLASK_ENV"] == "development":
        common_style_bundle.build()
        auth_style_bundle.build()
        user_style_bundle.build()
        playlist_style_bundle.build()
        recs_style_bundle.build()

        common_js_bundle.build()
        auth_js_bundle.build()
        user_js_bundle.build()
        playlist_js_bundle.build()
        recs_js_bundle.build()
    else:
        pass

    return assets
