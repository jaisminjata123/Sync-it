/* eslint-disable import/no-anonymous-default-export */
import "./App.css";
import SpotifyToYoutube from "./SpotifyToYoutube/";
import YoutubeToSpotify from "./YoutubeToSpotify/";
import Verified from "./Verified";
import {
  Switch,
  Route,
  Redirect,
  BrowserRouter as Router,
} from "react-router-dom";
import YoutubeVerified from "./YoutubeVerified";

export default () => {
  return (
    <>
      <Router>
        <Switch>
          <Route exact path="/">
            <Redirect to={{ pathname: "/yt2sp" }} />
          </Route>
          <Route path="/sp2yt">
            <SpotifyToYoutube />
          </Route>
          <Route path="/yt2sp">
            <YoutubeToSpotify />
          </Route>
          <Route path="/auth/spotify/callback">
            <Verified />
          </Route>
          <Route path="/google/verified">
            <YoutubeVerified />
          </Route>
          <Route render={() => <Redirect to="/" />} />
        </Switch>
      </Router>
    </>
  );
};
