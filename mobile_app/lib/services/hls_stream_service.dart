class HlsStreamService {
  static const String masterStreamUrl =
      'https://teknofest-arge-turkcell.ercdn.net/hls/4/pZ/faz2/faz2.smil/playlist.m3u8';

  // Master playlistte yayınlanan resmî varyantlar.
  static const String highQualityStreamUrl =
      'https://teknofest-arge-turkcell.ercdn.net/hls/4/pZ/faz2/faz2.smil/hlssubplaylist-ovbn2Ur8_oacnUA.m3u8';
  static const String lowQualityStreamUrl =
      'https://teknofest-arge-turkcell.ercdn.net/hls/4/pZ/faz2/faz2.smil/hlssubplaylist-ovdncBeb_oacnUA.m3u8';

  String getStreamUrl({required bool isQoDActive}) {
    return isQoDActive ? highQualityStreamUrl : lowQualityStreamUrl;
  }
}
