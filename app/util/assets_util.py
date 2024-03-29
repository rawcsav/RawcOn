from flask_assets import Bundle


def compile_static_assets(assets):
    common_style_bundle = Bundle("src/*.css", filters="cssmin", output="dist/css/common.css")
    auth_style_bundle = Bundle("auth/landing.css", filters="cssmin", output="dist/css/auth.css")
    user_style_bundle = Bundle("user/profile.css", filters="cssmin", output="dist/css/user.css")
    playlist_style_bundle = Bundle("playlist/playlist.css", filters="cssmin", output="dist/css/playlist.css")
    spec_playlist_style_bundle = Bundle(
        "playlist/spec_playlist.css", filters="cssmin", output="dist/css/spec_playlist.css"
    )
    recs_style_bundle = Bundle("recs/recs.css", filters="cssmin", output="dist/css/recs.css")
    stats_style_bundle = Bundle("stats/stats.css", filters="cssmin", output="dist/css/stats.css")

    assets.register("common_style_bundle", common_style_bundle)
    assets.register("auth_style_bundle", auth_style_bundle)
    assets.register("user_style_bundle", user_style_bundle)
    assets.register("playlist_style_bundle", playlist_style_bundle)
    assets.register("spec_playlist_style_bundle", spec_playlist_style_bundle)
    assets.register("recs_style_bundle", recs_style_bundle)
    assets.register("stats_style_bundle", stats_style_bundle)

    common_js_bundle = Bundle("src/*.js", filters="jsmin", output="dist/js/common.js")
    auth_js_bundle = Bundle("auth/*.js", filters="jsmin", output="dist/js/auth.js")
    user_js_bundle = Bundle("user/*.js", filters="jsmin", output="dist/js/user.js")
    playlist_js_bundle = Bundle("playlist/playlist.js", filters="jsmin", output="dist/js/playlist.js")
    spec_playlist_js_bundle = Bundle("playlist/spec_playlist.js", filters="jsmin", output="dist/js/spec_playlist.js")
    recs_js_bundle = Bundle("recs/*.js", filters="jsmin", output="dist/js/recs.js")
    stats_js_bundle = Bundle("stats/*.js", filters="jsmin", output="dist/js/stats.js")

    assets.register("common_js_bundle", common_js_bundle)
    assets.register("auth_js_bundle", auth_js_bundle)
    assets.register("user_js_bundle", user_js_bundle)
    assets.register("playlist_js_bundle", playlist_js_bundle)
    assets.register("spec_playlist_js_bundle", spec_playlist_js_bundle)
    assets.register("recs_js_bundle", recs_js_bundle)
    assets.register("stats_js_bundle", stats_js_bundle)

    if assets.config["FLASK_ENV"] == "development":
        common_style_bundle.build()
        auth_style_bundle.build()
        user_style_bundle.build()
        playlist_style_bundle.build()
        spec_playlist_style_bundle.build()
        recs_style_bundle.build()
        stats_style_bundle.build()

        common_js_bundle.build()
        auth_js_bundle.build()
        user_js_bundle.build()
        playlist_js_bundle.build()
        spec_playlist_js_bundle.build()
        recs_js_bundle.build()
        stats_js_bundle.build()
    else:
        pass

    return assets
